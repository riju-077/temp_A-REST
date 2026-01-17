make a python fastapi project everything is giving below how it should be also make sure that i use uv and not pip also main.py file should be written in such a manner that when i run uv run main.py it should run

Like for now lets create this endpoints using list and lets not focus on database ok whatever we need to do update delete or whatever we will do it considering list for the timebeing or if there is a better alternative then just say it i will decide and for the pydantic part make a different file or folder so that its understanble so that it reduces redandency and makes the code structure look good and understanble

GET
List of all objects

Response
[
   {
      "id": "1",
      "name": "Google Pixel 6 Pro",
      "data": {
         "color": "Cloudy White",
         "capacity": "128 GB"
      }
   },
   {
      "id": "2",
      "name": "Apple iPhone 12 Mini, 256GB, Blue",
      "data": null
   },
   {
      "id": "3",
      "name": "Apple iPhone 12 Pro Max",
      "data": {
         "color": "Cloudy White",
         "capacity GB": 512
      }
   },
   {
      "id": "4",
      "name": "Apple iPhone 11, 64GB",
      "data": {
         "price": 389.99,
         "color": "Purple"
      }
   },
   {
      "id": "5",
      "name": "Samsung Galaxy Z Fold2",
      "data": {
         "price": 689.99,
         "color": "Brown"
      }
   },
   {
      "id": "6",
      "name": "Apple AirPods",
      "data": {
         "generation": "3rd",
         "price": 120
      }
   },
   {
      "id": "7",
      "name": "Apple MacBook Pro 16",
      "data": {
         "year": 2019,
         "price": 1849.99,
         "CPU model": "Intel Core i9",
         "Hard disk size": "1 TB"
      }
   },
   {
      "id": "8",
      "name": "Apple Watch Series 8",
      "data": {
         "Strap Colour": "Elderberry",
         "Case Size": "41mm"
      }
   },
   {
      "id": "9",
      "name": "Beats Studio3 Wireless",
      "data": {
         "Color": "Red",
         "Description": "High-performance wireless noise cancelling headphones"
      }
   },
   {
      "id": "10",
      "name": "Apple iPad Mini 5th Gen",
      "data": {
         "Capacity": "64 GB",
         "Screen size": 7.9
      }
   },
   {
      "id": "11",
      "name": "Apple iPad Mini 5th Gen",
      "data": {
         "Capacity": "254 GB",
         "Screen size": 7.9
      }
   },
   {
      "id": "12",
      "name": "Apple iPad Air",
      "data": {
         "Generation": "4th",
         "Price": "419.99",
         "Capacity": "64 GB"
      }
   },
   {
      "id": "13",
      "name": "Apple iPad Air",
      "data": {
         "Generation": "4th",
         "Price": "519.99",
         "Capacity": "256 GB"
      }
   }
]
--------------------------------------------------------------------
GET
List of objects by ids

Response
[
   {
      "id": "3",
      "name": "Apple iPhone 12 Pro Max",
      "data": {
         "color": "Cloudy White",
         "capacity GB": 512
      }
   },
   {
      "id": "5",
      "name": "Samsung Galaxy Z Fold2",
      "data": {
         "price": 689.99,
         "color": "Brown"
      }
   },
   {
      "id": "10",
      "name": "Apple iPad Mini 5th Gen",
      "data": {
         "Capacity": "64 GB",
         "Screen size": 7.9
      }
   }
]
--------------------------------------------------------------------
GET
Single object

Response
{
   "id": "7",
   "name": "Apple MacBook Pro 16",
   "data": {
      "year": 2019,
      "price": 1849.99,
      "CPU model": "Intel Core i9",
      "Hard disk size": "1 TB"
   }
}
------------------------------------------------------------------
POST
Add object

Request
{
   "name": "Apple MacBook Pro 16",
   "data": {
      "year": 2019,
      "price": 1849.99,
      "CPU model": "Intel Core i9",
      "Hard disk size": "1 TB"
   }
}

Response
{
   "id": "7",
   "name": "Apple MacBook Pro 16",
   "data": {
      "year": 2019,
      "price": 1849.99,
      "CPU model": "Intel Core i9",
      "Hard disk size": "1 TB"
   },
   "createdAt": "2022-11-21T20:06:23.986Z"
}
---------------------------------------------------------------------------
PUT
Update object

Request
{
   "name": "Apple MacBook Pro 16",
   "data": {
      "year": 2019,
      "price": 2049.99,
      "CPU model": "Intel Core i9",
      "Hard disk size": "1 TB",
      "color": "silver"
   }
}

Response
{
   "id": "7",
   "name": "Apple MacBook Pro 16",
   "data": {
      "year": 2019,
      "price": 2049.99,
      "CPU model": "Intel Core i9",
      "Hard disk size": "1 TB",
      "color": "silver"
   },
   "updatedAt": "2022-12-25T21:08:41.986Z"
}
------------------------------------------------------------------
PATCH
Partially update object

Request
{
   "name": "Apple MacBook Pro 16 (Updated Name)"
}

Response
{
   "id": "7",
   "name": "Apple MacBook Pro 16 (Updated Name)",
   "data": {
      "year": 2019,
      "price": 1849.99,
      "CPU model": "Intel Core i9",
      "Hard disk size": "1 TB"
   },
   "updatedAt": "2022-12-25T21:09:46.986Z"
}
------------------------------------------------------------------------------------------
DELETE
Delete object

Response
{
   "message": "Object with id = 6, has been deleted."
}
--------------------------------------------------