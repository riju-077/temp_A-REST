# SQL Thinking Guide — How to Tackle Big Queries
Written for Akash — a practical guide with examples

---

## Part 1: The Carpenter Method (5 Steps to Handle Any Big Query)

Imagine a carpenter fixing a desk. He doesn't rebuild the whole thing.
He inspects it, finds where the fix goes, copies a similar part, tests it, done.

Same thing with big SQL queries.

---

### Step 1: Read CTE Names Only (Look at the Desk's Shape)

DON'T read the SQL inside each CTE. Just read the NAMES.

Example — the deep_q_sp_bid() query has these CTEs:
```
MAIN_TAB           → Config (which campaigns are turned on)
KEY_TAB            → Keywords we're managing
SQS_TAB            → Today's raw traffic data
CURR_TAB           → Current round numbers
PREV_TAB           → Previous round numbers
TOTAL_CLICK_TAB    → Clicks over last X hours
TOTAL_CONV_TAB     → Conversions over last X hours
CONV_TAB           → Store-level orders (last hour)
LATEST_CPC_TAB     → Most recent paid click timestamp
CPC_CURR_TAB       → CPC at latest timestamp
CPC_PREV_TAB       → CPC at the one before that
COST_TAB           → Total spend per campaign
KEY_CONV_TAB       → Conversions per keyword (current)
PREV_KEY_CONV_TAB  → Conversions per keyword (previous)
FINAL_TAB          → Everything merged into one row per keyword
```

Now you have a MAP. You know what each piece does without reading any code.

Think of it like looking at a building from outside:
- Ground floor = data sources (MAIN_TAB, SQS_TAB)
- Middle floors = calculations (CURR_TAB, PREV_TAB, CVR, CPC)
- Top floor = final merge (FINAL_TAB)

---

### Step 2: Find Where Your New Piece Connects

Ask yourself 3 questions:
1. What SOURCE TABLE has the data I need?
2. What LEVEL do I need it at? (per keyword? per campaign? per placement?)
3. Which CTE is the FINAL ASSEMBLY POINT where I plug it in?

Example for "add last hour impressions":
1. Source table → AS_SP_TRAFFIC (that's where impressions live)
2. Level → per KEYWORD + per PLACEMENT (because I need TOS/PP/ROS separately)
3. Assembly point → FINAL_TAB (that's where everything comes together)

---

### Step 3: Copy a Similar Existing CTE and Tweak

NEVER write from scratch. Find a CTE that already does something similar.

Example — I needed: SUM of IMPRESSIONS from AS_SP_TRAFFIC for last 1 hour

I found TOTAL_CLICK_TAB already does: SUM of CLICKS from AS_SP_TRAFFIC for last X hours

```sql
-- ORIGINAL (TOTAL_CLICK_TAB)
SELECT KEYWORD_ID, SUM(CLICKS) AS CLICKS
FROM AS_SP_TRAFFIC
WHERE CAST(TIME_WINDOW_START AS DATETIME2) >= DATEADD(HOUR, -@CVRDAYCOUNT, @NOW)
GROUP BY KEYWORD_ID
```

3 tweaks:
- SUM(CLICKS) → SUM(IMPRESSIONS)        ... different column
- -@CVRDAYCOUNT → -1                     ... different time window
- GROUP BY add PLACEMENT                  ... need per-placement breakdown

```sql
-- NEW (LAST_HOUR_IMP_TAB)
SELECT KEYWORD_ID, PLACEMENT, SUM(IMPRESSIONS) AS LAST_HOUR_IMP
FROM AS_SP_TRAFFIC
WHERE CAST(TIME_WINDOW_START AS DATETIME2) BETWEEN DATEADD(HOUR, -1, @NOW) AND @NOW
GROUP BY KEYWORD_ID, PLACEMENT
```

Copy → Tweak → Done. No reinventing.

---

### Step 4: Test Your New CTE Alone

Before plugging into the big query, run JUST your new CTE:

```sql
DECLARE @NOW DATETIME = '2024-08-01 10:00:00';

WITH LAST_HOUR_IMP_TAB AS (
    SELECT KEYWORD_ID, PLACEMENT, SUM(IMPRESSIONS) AS LAST_HOUR_IMP
    FROM [AMAZON_MARKETING].[DBO].AS_SP_TRAFFIC
    WHERE CAST(TIME_WINDOW_START AS DATETIME2) BETWEEN DATEADD(HOUR, -1, @NOW) AND @NOW
    GROUP BY KEYWORD_ID, PLACEMENT
)
SELECT * FROM LAST_HOUR_IMP_TAB
```

Check:
- Does it return data? (not empty?)
- Do the numbers make sense? (not millions when you expect hundreds?)
- Are the columns right? (KEYWORD_ID, PLACEMENT, LAST_HOUR_IMP?)

If yes → safe to plug in.

---

### Step 5: Compare Row Counts Before and After

After plugging your new CTE into the big query:

```sql
-- Run original query
SELECT COUNT(*) FROM FINAL_TAB   -- say it returns 150

-- Run your modified query
SELECT COUNT(*) FROM FINAL_TAB   -- should also return 150
```

Same count? → Your LEFT JOIN didn't break anything.
Different count? → Your join is duplicating or dropping rows. Something's wrong.

---

## Part 2: The CASE + SUM Pivot Trick (Turning Rows Into Columns)

### The Problem

You have data like this (multiple rows per keyword):

```
LAST_HOUR_IMP_TAB (input):
┌────────────┬──────────────────────────────┬───────────────┐
│ KEYWORD_ID │ PLACEMENT                    │ LAST_HOUR_IMP │
├────────────┼──────────────────────────────┼───────────────┤
│ 555        │ Top of Search on-Amazon      │ 200           │
│ 555        │ Detail Page on-Amazon        │ 80            │
│ 555        │ Other on-Amazon              │ 45            │
│ 777        │ Top of Search on-Amazon      │ 150           │
│ 777        │ Other on-Amazon              │ 30            │
└────────────┴──────────────────────────────┴───────────────┘
```

But FINAL_TAB needs ONE row per keyword with THREE columns.

### The Solution — CASE + SUM

```sql
SELECT KEYWORD_ID,
    ISNULL(SUM(CASE WHEN UPPER(PLACEMENT) = 'TOP OF SEARCH ON-AMAZON'
                    THEN LAST_HOUR_IMP END), 0) AS TOS_LAST_HOUR_IMP,
    ISNULL(SUM(CASE WHEN UPPER(PLACEMENT) = 'DETAIL PAGE ON-AMAZON'
                    THEN LAST_HOUR_IMP END), 0) AS PP_LAST_HOUR_IMP,
    ISNULL(SUM(CASE WHEN UPPER(PLACEMENT) = 'OTHER ON-AMAZON'
                    THEN LAST_HOUR_IMP END), 0) AS ROS_LAST_HOUR_IMP
FROM LAST_HOUR_IMP_TAB
GROUP BY KEYWORD_ID
```

### How It Works — Row by Row for Keyword 555

Think of 3 buckets on a table, labeled TOS, PP, and ROS.
Each row walks up and drops its number into the matching bucket.

**Row 1 walks up:** PLACEMENT = "Top of Search on-Amazon", value = 200

| Check               | Match? | TOS bucket | PP bucket | ROS bucket |
|----------------------|--------|------------|-----------|------------|
| = TOP OF SEARCH?     | YES    | gets 200   |           |            |
| = DETAIL PAGE?       | NO     |            | gets NULL  |            |
| = OTHER?             | NO     |            |           | gets NULL   |

**Row 2 walks up:** PLACEMENT = "Detail Page on-Amazon", value = 80

| Check               | Match? | TOS bucket | PP bucket | ROS bucket |
|----------------------|--------|------------|-----------|------------|
| = TOP OF SEARCH?     | NO     | gets NULL  |           |            |
| = DETAIL PAGE?       | YES    |            | gets 80    |            |
| = OTHER?             | NO     |            |           | gets NULL   |

**Row 3 walks up:** PLACEMENT = "Other on-Amazon", value = 45

| Check               | Match? | TOS bucket | PP bucket | ROS bucket |
|----------------------|--------|------------|-----------|------------|
| = TOP OF SEARCH?     | NO     | gets NULL  |           |            |
| = DETAIL PAGE?       | NO     |            | gets NULL  |            |
| = OTHER?             | YES    |            |           | gets 45     |

**Now SUM each bucket (SUM ignores NULLs):**

```
TOS bucket: 200 + NULL + NULL = 200
PP bucket:  NULL + 80 + NULL  = 80
ROS bucket: NULL + NULL + 45  = 45
```

**Result for keyword 555: ONE row, THREE columns.**

### Now Keyword 777 (Missing Detail Page)

Only 2 rows: TOS=150, ROS=30. No Detail Page row exists.

```
TOS bucket: 150
PP bucket:  (no rows dropped anything in) = NULL
ROS bucket: 30
```

SUM of nothing = NULL. Then ISNULL(NULL, 0) = 0.

**Result for keyword 777:**

### Final Output

```
LAST_HOUR_PIVOT_TAB (output):
┌────────────┬───────────────────┬──────────────────┬───────────────────┐
│ KEYWORD_ID │ TOS_LAST_HOUR_IMP │ PP_LAST_HOUR_IMP │ ROS_LAST_HOUR_IMP │
├────────────┼───────────────────┼──────────────────┼───────────────────┤
│ 555        │ 200               │ 80               │ 45                │
│ 777        │ 150               │ 0                │ 30                │
└────────────┴───────────────────┴──────────────────┴───────────────────┘
```

3 rows per keyword → 1 row per keyword. That's the pivot.

### Why SUM and Not Just CASE?

Because GROUP BY KEYWORD_ID collapses multiple rows into one.
When you collapse rows, SQL needs an aggregate function (SUM, MAX, COUNT, etc.).

- CASE alone returns one value per ROW
- SUM(CASE ...) returns one value per GROUP

Without SUM, SQL would say: "You gave me 3 rows for keyword 555 but want 1 row. I don't know which value to pick!" SUM tells it: "Add them up."

And since only ONE row per group matches each CASE (TOS row only matches TOS check),
SUM is really just picking up that ONE value and ignoring the NULLs.

### Quick Analogy

Imagine a post office with 3 mailboxes: TOS, PP, ROS.

The mail carrier (SQL) has 3 letters (rows) for keyword 555:
- Letter 1 (TOS letter) → goes into TOS mailbox
- Letter 2 (PP letter)  → goes into PP mailbox
- Letter 3 (ROS letter) → goes into ROS mailbox

At the end of the day, you open each mailbox and COUNT what's inside.
That's SUM(CASE WHEN ...).

If no letter came for a mailbox? It's empty = NULL = ISNULL turns it to 0.

### When to Use This Trick

Anytime you need to turn ROWS into COLUMNS:
- Multiple placements per keyword → one column per placement
- Multiple dates per product → one column per date
- Multiple categories per user → one column per category

The pattern is always the same:
```sql
SUM(CASE WHEN [category_column] = 'value1' THEN [number_column] END) AS column1,
SUM(CASE WHEN [category_column] = 'value2' THEN [number_column] END) AS column2,
SUM(CASE WHEN [category_column] = 'value3' THEN [number_column] END) AS column3
```

Copy this pattern. Change the column names. Done.
