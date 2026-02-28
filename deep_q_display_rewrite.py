"""
REWRITE of deep_q_display() — separate file, original NOT touched.

CHANGES from original (lines 712-1141 of deep_q_24.py):
1. SQL QUERY: Added LAST_HOUR_IMP CTE + 3 new columns (TOS_LAST_HOUR_IMP, PP_LAST_HOUR_IMP, ROS_LAST_HOUR_IMP)
   - All 3 get the SAME value (total impressions) since AS_SD_TRAFFIC has no PLACEMENT column
2. DIMENSIONS: 6 → 9 inputs (added 3 impression inputs)
3. STATE VECTORS: All 4 places updated from 6 numbers to 9 numbers
   - pending_buffer_update_data (next_state)
   - global_pending_buffer_update_data (next_state)
   - select_action (state)
   - temp_buffer_list (state)
4. Nothing else changed — reward formulas, bid logic, CVR safety valve, logging all stay the same.

NOTE: When deploying this, you MUST delete the old SD .pth and .pkl files
      (old brain has 6 inputs, new brain needs 9 — shapes won't match).
"""


def deep_q_display(interval: int, monitor: bool):

    # ======================== STEP 1: SQL QUERY ========================
    sql_data = qcm.fetch(
        f"""
DECLARE @NOW DATETIME = '{pst_time_str()}',
	@INTERVAL INT = {interval},
	@MONITOR BIT = {int(monitor)};
DECLARE @STARTOFHOUR DATETIME2 = CAST(FORMAT(@NOW, 'yyyy-MM-dd HH:00') AS DATETIME2);
DECLARE @CVRDAYCOUNT INT = (SELECT MAX(CVRDAYCOUNT) FROM MODELING_DB.DBO.Q_MASTER
    WHERE DEEPQSWITCH = 1 AND CAMPAIGNTYPE = 'SD');

WITH MAIN_TAB AS (
        SELECT * FROM MODELING_DB.DBO.Q_MASTER
        WHERE DEEPQSWITCH = 1 AND CAMPAIGNTYPE = 'SD'),
KEY_TAB AS (
        SELECT * FROM MODELING_DB.DBO.KEYWORDS_FOR_AGENT
        WHERE CAMPAIGNID IN (SELECT CAMPAIGNID FROM MAIN_TAB)),
SQS_TAB AS (
	SELECT CAMPAIGN_ID, TARGET_ID, CLICKS, IMPRESSIONS, COST, DATATIME
	FROM [AMAZON_ANALYTICS].[DBO].AS_SD_TRAFFIC
	WHERE CAST(TIME_WINDOW_START AS DATE) = CAST(@NOW AS DATE)
		AND DATATIME <= @NOW AND CAMPAIGN_ID IN (SELECT CAMPAIGNID FROM MAIN_TAB)
	),
CURR_TAB AS (
	SELECT TARGET_ID, SUM(CLICKS) CLK0, SUM(IMPRESSIONS) IMP0,  SUM(CAST(COST AS FLOAT)) COST0,
		CASE WHEN SUM(CLICKS) = 0 THEN 0
		ELSE CAST(SUM(COST) AS FLOAT)/SUM(CLICKS) END AS CPC,
        CASE WHEN SUM(IMPRESSIONS) = 0 THEN 0
            WHEN SUM(IMPRESSIONS) > 0 AND SUM(CLICKS) <= 0 THEN (1.0/SUM(IMPRESSIONS) - 1)
        ELSE CAST(SUM(CLICKS) AS FLOAT)/SUM(IMPRESSIONS) END AS CTR0
        FROM SQS_TAB GROUP BY TARGET_ID),
PREV_TAB AS (
        SELECT TARGET_ID, SUM(CLICKS) CLK1, SUM(IMPRESSIONS) IMP1,
		CASE WHEN SUM(CLICKS) = 0 THEN 0
		ELSE CAST(SUM(COST) AS FLOAT)/SUM(CLICKS) END AS CPC1,
            CASE WHEN SUM(IMPRESSIONS) = 0 THEN 0 WHEN SUM(IMPRESSIONS) > 0 AND SUM(CLICKS) <= 0 THEN (1.0/SUM(IMPRESSIONS) - 1)
        ELSE CAST(SUM(CLICKS) AS FLOAT)/SUM(IMPRESSIONS) END AS CTR1
        FROM SQS_TAB WHERE DATATIME <= DATEADD(MINUTE, -@INTERVAL, @NOW)
        GROUP BY TARGET_ID),
TOTAL_CLICK_TAB AS (
		SELECT TARGET_ID, SUM(CLICKS) AS CLICKS FROM [AMAZON_ANALYTICS].[DBO].AS_SD_TRAFFIC
		WHERE CAST(TIME_WINDOW_START AS DATETIME2) >= DATEADD(HOUR, -@CVRDAYCOUNT, @NOW) AND CAST(DATATIME AS DATE) <= @NOW
			AND CAMPAIGN_ID IN (SELECT CAMPAIGNID FROM MAIN_TAB)
		GROUP BY TARGET_ID),
TOTAL_CONV_TAB AS (
		SELECT TARGET_ID, SUM(ATTRIBUTED_CONVERSIONS_14D) AS CONVERSION FROM [AMAZON_ANALYTICS].[DBO].AS_SD_CONVERSION
		WHERE CAST(TIME_WINDOW_START AS DATETIME2) >= DATEADD(HOUR, -@CVRDAYCOUNT, @NOW) AND CAST(DATATIME AS DATE) <= @NOW
			AND CAMPAIGN_ID IN (SELECT CAMPAIGNID FROM MAIN_TAB)
		GROUP BY TARGET_ID),
CONV_TAB AS (
		SELECT SUM(CONVERSION) AS UNITS
		FROM (
			SELECT ISNULL(ORDERCOUNT - LAG(ORDERCOUNT) OVER (PARTITION BY CAST(TIMESTAMP AS DATE) ORDER BY TIMESTAMP), 0) AS CONVERSION
			FROM [AMAZON_MARKETING].[DBO].[AMZN_SALES_DATA]
			WHERE TIMESTAMP >= DATEADD(HOUR, -1, @STARTOFHOUR)
			  AND TIMESTAMP <= @NOW
		) AS TAB),
LATEST_CPC_TAB AS (
	SELECT TARGET_ID, MAX(DATATIME) LATEST
	FROM SQS_TAB WHERE COST > 0 GROUP BY TARGET_ID),
CPC_CURR_TAB AS(
	SELECT ST.TARGET_ID, SUM(CAST(ST.COST AS FLOAT)) / SUM(ST.CLICKS) AS CPC FROM
	SQS_TAB ST JOIN LATEST_CPC_TAB LCT ON ST.TARGET_ID = LCT.TARGET_ID AND ST.DATATIME = LCT.LATEST AND ST.CLICKS > 0
	GROUP BY ST.TARGET_ID
	),
CPC_PREV_TAB AS(
	SELECT ST.TARGET_ID, SUM(CAST(ST.COST AS FLOAT)) / SUM(ST.CLICKS) AS CPC FROM
	SQS_TAB ST JOIN(
		SELECT ST.TARGET_ID, MAX(ST.DATATIME) PREV
		FROM SQS_TAB ST JOIN LATEST_CPC_TAB LCT
			ON ST.TARGET_ID=LCT.TARGET_ID AND ST.DATATIME < LCT.LATEST AND ST.COST > 0 AND ST.CLICKS > 0
		GROUP BY ST.TARGET_ID
	) PCT ON ST.TARGET_ID = PCT.TARGET_ID AND ST.DATATIME = PCT.PREV
	GROUP BY ST.TARGET_ID),
COST_TAB AS (
	SELECT CAMPAIGN_ID, SUM(CAST(COST AS FLOAT)) COST FROM SQS_TAB GROUP BY CAMPAIGN_ID),
KEY_CONV_TAB AS (
	SELECT TARGET_ID AS KEYWORDID , SUM(ATTRIBUTED_CONVERSIONS_14D) AS CONV FROM [AMAZON_ANALYTICS].[DBO].AS_SD_CONVERSION
		WHERE CAST(TIME_WINDOW_START AS DATE) >= CAST(@NOW AS DATE) AND DATATIME <= @NOW
			AND CAMPAIGN_ID IN (SELECT CAMPAIGNID FROM MAIN_TAB)
	GROUP BY TARGET_ID),
PREV_KEY_CONV_TAB AS (
	SELECT TARGET_ID AS KEYWORDID , SUM(ATTRIBUTED_CONVERSIONS_14D) AS PREV_CONV FROM [AMAZON_ANALYTICS].[DBO].AS_SD_CONVERSION
		WHERE CAST(TIME_WINDOW_START AS DATE) >= CAST(@NOW AS DATE) AND DATATIME <=  DATEADD(MINUTE, -@INTERVAL, @NOW)
			AND CAMPAIGN_ID IN (SELECT CAMPAIGNID FROM MAIN_TAB)
	GROUP BY TARGET_ID),
LAST_HOUR_IMP AS (
    SELECT TARGET_ID, SUM(IMPRESSIONS) AS L_HOUR_IMP
    FROM [AMAZON_ANALYTICS].[DBO].AS_SD_TRAFFIC
    WHERE DATATIME > DATEADD(MINUTE, -60, @NOW)
        AND DATATIME <= @NOW
        AND CAMPAIGN_ID IN (SELECT CAMPAIGNID FROM MAIN_TAB)
    GROUP BY TARGET_ID
    ),
FINAL_TAB AS (
	SELECT KT.KEYWORDID, KT.CAMPAIGNID, KT.ADGROUPID, MT.GAMMA, MT.LR, MT.EPSTART, MT.BASEBIDLOWER, MT.BASEBIDUPPER, MT.COMBINEDDEEPQSWITCH,
		MT.CVRFLAG, MT.CLICKSTEP, CASE WHEN TCV.CONVERSION>0 THEN CAST (TCLK.CLICKS AS FLOAT) / TCV.CONVERSION ELSE 0 END CVR,
        MT.CTRWEIGHT, MT.CONVWEIGHT, MT.CVRWEIGHT, MT.WEIGHTFLAG, MT.CPCWEIGHT, MT.BUDGETWEIGHT, MT.DYNAMICEXPLORE,
        MT.BOLTZFLAG, MT.TDECAY,
		ISNULL(ROUND(CT.CTR0,4),0) AS CURR_CTR,
		ROUND(ISNULL(CT.CTR0, 0) - ISNULL(PT.CTR1, 0), 4) AS DELTA_CTR,
		ISNULL(ROUND(CT.CPC,2),0) AS CPC, ISNULL(ROUND(PT.CPC1,2),0) AS CPC1, ISNULL(CVT.UNITS,0) UNITS,
        ISNULL(CCT.CPC, 0) CURR_CPC, ISNULL(CPT.CPC, 0) PREV_CPC,  ISNULL(CST.COST,0) SPENTBUDGET, ISNULL(KCT.CONV,0) CONV,
		ISNULL(PKCT.PREV_CONV,0) PREV_CONV, ISNULL(PT.CLK1,0) PREV_CLICK, ISNULL(CT.CLK0,0) CLICK, ISNULL(CT.COST0,0) COST,
        ISNULL(LHI.L_HOUR_IMP, 0) TOS_LAST_HOUR_IMP,
        ISNULL(LHI.L_HOUR_IMP, 0) PP_LAST_HOUR_IMP,
        ISNULL(LHI.L_HOUR_IMP, 0) ROS_LAST_HOUR_IMP
	FROM KEY_TAB KT LEFT JOIN CURR_TAB CT ON KT.KEYWORDID = CT.TARGET_ID
		LEFT JOIN MAIN_TAB MT ON KT.CAMPAIGNID = MT.CAMPAIGNID
		LEFT JOIN PREV_TAB PT ON KT.KEYWORDID = PT.TARGET_ID
		LEFT JOIN TOTAL_CLICK_TAB TCLK ON KT.KEYWORDID = TCLK.TARGET_ID
		LEFT JOIN TOTAL_CONV_TAB TCV ON KT.KEYWORDID = TCV.TARGET_ID
        LEFT JOIN CPC_CURR_TAB CCT ON KT.KEYWORDID = CCT.TARGET_ID
		LEFT JOIN CPC_PREV_TAB CPT ON KT.KEYWORDID = CPT.TARGET_ID
		LEFT JOIN COST_TAB CST ON KT.CAMPAIGNID = CST.CAMPAIGN_ID
		LEFT JOIN KEY_CONV_TAB KCT ON KT.KEYWORDID = KCT.KEYWORDID
        LEFT JOIN PREV_KEY_CONV_TAB PKCT ON KT.KEYWORDID = PKCT.KEYWORDID
        LEFT JOIN CONV_TAB CVT ON 1=1
        LEFT JOIN LAST_HOUR_IMP LHI ON KT.KEYWORDID = LHI.TARGET_ID)
SELECT * FROM FINAL_TAB
WHERE @MONITOR = 0 OR DELTA_CTR <= 0 --OR CPC <> CPC1
"""
    )

    # ======================== STEP 2: READ CONFIG ========================
    reward_distribution_list = [[0, 0, 0] for _ in range(100)]
    if sql_data == []:
        with open("sd_deepq.txt", "a") as f:
            f.write(pst_time_str() + "\n" + "No Data!" + "\n\n")
        return None, reward_distribution_list

    dynamic_explore = sql_data[0]["DYNAMICEXPLORE"]
    learning_rate = sql_data[0]["LR"]
    gamma = sql_data[0]["GAMMA"]
    epsilon = (
        sql_data[0]["EPSTART"]
        if not dynamic_explore
        else round(
            (min(0.99, sql_data[0]["EPSTART"]) ** (minute_from_last_reset / 60)), 2
        )
    )
    units = sql_data[0]["UNITS"]
    boltz_switch = sql_data[0]["BOLTZFLAG"]
    t_decay = sql_data[0]["TDECAY"]

    # Configuring the paths
    replay_buffer_path = path_dict["SD"]["replay_buffer_path"]
    temp_buffer_path = path_dict["SD"]["temp_buffer_path"]
    policy_model_path = path_dict["SD"]["policy_model_path"]
    target_model_path = path_dict["SD"]["target_model_path"]

    global_replay_buffer_path = path_dict["global"]["replay_buffer_path"]
    global_temp_buffer_path = path_dict["global"]["temp_buffer_path"]
    global_policy_model_path = path_dict["global"]["policy_model_path"]
    global_target_model_path = path_dict["global"]["target_model_path"]

    # Getting current bids from Amazon
    bid_dict = get_display_bids([k["KEYWORDID"] for k in sql_data])
    # Getting currently enabled campaignIds
    enabled_campaignids = get_enabled_display_campaigns(
        list({c["CAMPAIGNID"] for c in sql_data})
    )

    # ======================== STEP 3: PENDING BUFFER (DELAYED GRADING) ========================
    # ===>> Readying the data for updating pending buffers
    # CHANGED: next_state now has 9 numbers instead of 6 (added 3 impression inputs)
    pending_buffer_update_data = {
        r["KEYWORDID"]: {
            "next_state": torch.tensor(
                [
                    r["CURR_CTR"],
                    r["DELTA_CTR"],
                    r["CPC"],
                    bid_dict.get(r["KEYWORDID"], 0),
                    r["PREV_CPC"] - r["CURR_CPC"],
                    enabled_campaignids.get(r["CAMPAIGNID"], 1) - r["SPENTBUDGET"],
                    r["TOS_LAST_HOUR_IMP"],       # NEW input 7
                    r["PP_LAST_HOUR_IMP"],         # NEW input 8
                    r["ROS_LAST_HOUR_IMP"],        # NEW input 9
                ],
                dtype=torch.float32,
            ),
            "reward": r["CTRWEIGHT"] * r["DELTA_CTR"]
            + (
                r["BUDGETWEIGHT"]
                * (
                    negative_mapping(r["CONV"], r["CLICK"])
                    - negative_mapping(r["PREV_CONV"], r["PREV_CLICK"])
                )
            ),
        }
        for r in sql_data
        if bid_dict.get(r["KEYWORDID"], 0) >= 0.3
        and r["CAMPAIGNID"] in enabled_campaignids
    }
    global_pending_buffer_update_data = {}

    # Creating temporary buffer instant & updating the pending values
    temp_buffer = PersistentReplayBuffer(temp_buffer_path)
    temp_buffer.update(replay_buffer_path, pending_buffer_update_data)

    # ======================== STEP 4: CREATE 2 BRAINS ========================
    # CHANGED: dimensions from [6, ...] to [9, ...]
    if policy_model_path == "./":
        dimensions = [9, 64, 64, 64, 64, 64, 64, 79]
        policy_model_path += "starting_model_sd_" + config_time_for_file_name() + ".pth"
    else:
        dimensions = get_dimensions_from_file("dqn_models", policy_model_path)

    if global_policy_model_path == "./":
        global_dimensions = [9, 64, 64, 64, 64, 64, 64, 79]
        global_policy_model_path += (
            "starting_model_global_" + config_time_for_file_name() + ".pth"
        )
    else:
        global_dimensions = get_dimensions_from_file(
            "dqn_models", global_policy_model_path
        )

    # ===>> Creating DQN agent
    dqn_agent = DQNAgent(
        dimensions=dimensions,
        replay_path=replay_buffer_path,
        temp_replay_path=temp_buffer_path,
        policy_net_path=policy_model_path,
        target_net_path=target_model_path,
        epsilon_start=epsilon,
        gamma=gamma,
        lr=learning_rate,
        campaignType="SD",
        boltz_switch=boltz_switch,
        t_decay=t_decay,
        t_start=1,
        t_end=0.1,
    )

    global_dqn_agent = DQNAgent(
        dimensions=global_dimensions,
        replay_path=global_replay_buffer_path,
        temp_replay_path=global_temp_buffer_path,
        policy_net_path=global_policy_model_path,
        target_net_path=global_target_model_path,
        lr=learning_rate,
        epsilon_start=epsilon,
        gamma=gamma,
        boltz_switch=boltz_switch,
        t_decay=t_decay,
        t_start=1,
        t_end=0.1,
    )
    loss_log = []

    # ======================== STEP 5: TRAINING ========================
    # Training the network for 5 iterations
    for _ in range(5):
        loss_1 = dqn_agent.train_step()
        loss_2 = global_dqn_agent.train_step()
        if loss_1 is not None:
            loss_log.append({"agent": "SD", "loss": loss_1})
        if loss_2 is not None:
            loss_log.append({"agent": "GLOBAL", "loss": loss_2})
    # Saving models
    dqn_agent.save_models()
    global_dqn_agent.save_models()

    # ======================== STEP 6: ACTION SELECTION LOOP ========================
    # ===>> Taking actions
    bid_update_list = []
    temp_buffer_list = []
    log = []

    for row in sql_data:
        keywordId = row["KEYWORDID"]
        adGroupId = row["ADGROUPID"]
        campaignId = row["CAMPAIGNID"]
        bid = bid_dict.get(keywordId, 0)
        cvr_condition = row["CVRFLAG"]
        global_deep_q = row["COMBINEDDEEPQSWITCH"]
        weight_flag = row["WEIGHTFLAG"]
        del_cpc = row["PREV_CPC"] - row["CURR_CPC"]
        budget = enabled_campaignids.get(campaignId, 1)

        max_cvr = 100
        if row["CVR"] <= row["CLICKSTEP"]:
            normalized_cvr = 0
        elif row["CVR"] >= 100:
            normalized_cvr = 1
        else:
            normalized_cvr = (row["CVR"] - row["CLICKSTEP"]) / (
                max_cvr - row["CLICKSTEP"]
            )

        if bid >= 0.3 and campaignId in enabled_campaignids:
            del_cvr = negative_mapping(row["CONV"], row["CLICK"]) - negative_mapping(
                row["PREV_CONV"], row["PREV_CLICK"]
            )
            reward = (
                (row["CTRWEIGHT"] * row["DELTA_CTR"])
                + (row["CONVWEIGHT"] * units / 10)
                + (
                    row["CPCWEIGHT"]
                    * (del_cpc / row["PREV_CPC"] if row["PREV_CPC"] > 0 else 0)
                )
                + (row["CVRWEIGHT"] * negative_mapping(row["CONV"], row["CLICK"]))
                # + (row["BUDGETWEIGHT"] * (budget - row["COST"]) / budget)
                + (row["BUDGETWEIGHT"] * (del_cvr))
                if weight_flag
                else row["DELTA_CTR"] + units / 10
            )

            reward_distribution_list[decide_bucket(reward, -1, 1, 100)][0] += 1
            reward_distribution_list[decide_bucket(row["DELTA_CTR"], -1, 1, 100)][
                1
            ] += 1
            reward_distribution_list[decide_bucket(del_cvr, -1, 1, 100)][2] += 1

            # CHANGED: global next_state now has 9 numbers instead of 6
            global_pending_buffer_update_data.update(
                {
                    keywordId: {
                        "next_state": torch.tensor(
                            [
                                row["CURR_CTR"],
                                row["DELTA_CTR"],
                                row["CPC"],
                                bid,
                                del_cpc,
                                budget - row["SPENTBUDGET"],
                                row["TOS_LAST_HOUR_IMP"],       # NEW input 7
                                row["PP_LAST_HOUR_IMP"],         # NEW input 8
                                row["ROS_LAST_HOUR_IMP"],        # NEW input 9
                            ],
                            dtype=torch.float32,
                        ),
                        "reward": reward,
                    }
                }
            )

        # Only taking actions if bid >= 0.3
        if bid >= 0.3 and campaignId in enabled_campaignids:
            # CHANGED: select_action now gets 9 numbers instead of 6
            action = (
                dqn_agent.select_action(
                    [
                        row["CURR_CTR"],
                        row["DELTA_CTR"],
                        row["CPC"],
                        bid,
                        del_cpc,
                        budget - row["SPENTBUDGET"],
                        row["TOS_LAST_HOUR_IMP"],       # NEW input 7
                        row["PP_LAST_HOUR_IMP"],         # NEW input 8
                        row["ROS_LAST_HOUR_IMP"],        # NEW input 9
                    ]
                )
                if not global_deep_q
                else global_dqn_agent.select_action(
                    [
                        row["CURR_CTR"],
                        row["DELTA_CTR"],
                        row["CPC"],
                        bid,
                        del_cpc,
                        budget - row["SPENTBUDGET"],
                        row["TOS_LAST_HOUR_IMP"],       # NEW input 7
                        row["PP_LAST_HOUR_IMP"],         # NEW input 8
                        row["ROS_LAST_HOUR_IMP"],        # NEW input 9
                    ]
                )
            )
            calculated_bid = bid_from_action(0.3, 0.2, action)

            # Sick joke of bounding the bid
            capped_bid = round(
                min(max(calculated_bid, row["BASEBIDLOWER"]), row["BASEBIDUPPER"]), 2
            )
            capped_action = action_from_bid(0.3, 0.2, capped_bid)

            if cvr_condition:
                if random.uniform(0, 1) > normalized_cvr:
                    app_bid = capped_bid
                else:
                    app_bid = 0.3
                    capped_action = 0
                    log.append(
                        {
                            "keywordId": keywordId,
                            "cvrn": True,
                            "prevBid": bid,
                        }
                    )

            else:
                app_bid = capped_bid

            # ======================== STEP 7: PUSH TO AMAZON ========================
            # For updating bid in Amazon
            bid_update_list.append(
                {
                    "campaignId": campaignId,
                    "adGroupId": adGroupId,
                    "targetId": keywordId,
                    "bid": app_bid,
                }
            )
            # CHANGED: temp_buffer state now has 9 numbers instead of 6
            # Creating buffer for new buffer acquisition in Temporary Buffer file
            temp_buffer_list.append(
                {
                    "unique_id": keywordId,
                    "state": torch.tensor(
                        [
                            row["CURR_CTR"],
                            row["DELTA_CTR"],
                            row["CPC"],
                            bid,
                            del_cpc,
                            budget - row["SPENTBUDGET"],
                            row["TOS_LAST_HOUR_IMP"],       # NEW input 7
                            row["PP_LAST_HOUR_IMP"],         # NEW input 8
                            row["ROS_LAST_HOUR_IMP"],        # NEW input 9
                        ],
                        dtype=torch.float32,
                    ),
                    "action": capped_action,
                    "next_state": None,
                    "reward": None,
                    "done": False,
                }
            )

    global_temp_buffer = PersistentReplayBuffer(global_temp_buffer_path)
    global_temp_buffer.update(
        global_replay_buffer_path, global_pending_buffer_update_data
    )

    if bid_update_list:
        sd.UPDATE_KEYWORDS_SD(bid_update_list)

    if temp_buffer_list:
        temp_buffer.store(temp_buffer_list)
        global_temp_buffer.store(temp_buffer_list)

    # ======================== STEP 8: LOGGING ========================
    batch_rewards = [v["reward"] for v in global_pending_buffer_update_data.values()]
    avg_reward = sum(batch_rewards) / len(batch_rewards) if batch_rewards else None

    individual_loss = [item["loss"] for item in loss_log if item["agent"] == "SD"]
    avg_sv_loss = sum(individual_loss) / len(individual_loss) if individual_loss else 0

    global_loss = [item["loss"] for item in loss_log if item["agent"] == "GLOBAL"]
    avg_global_loss = sum(global_loss) / len(global_loss) if global_loss else 0

    loss_log = {"Individual": avg_sv_loss, "Global": avg_global_loss}

    with open("sd_deepq.txt", "a") as f:
        f.write(
            pst_time_str()
            + "\n"
            + str(bid_update_list)
            + "\n"
            + str(log)
            + "\n"
            + str(loss_log)
            + "\n\n"
        )

    return avg_reward, reward_distribution_list
