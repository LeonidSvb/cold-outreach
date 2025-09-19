@echo off
echo === Instantly API Test ===
echo.

set "API_KEY=YzZlYTFiZmQtNmZhYy00ZTQxLTkyNWMtNDYyODQ3N2UyOTU0OnpoTXlidndIZ3JuZQ=="

echo Testing API connection...
echo API Key (first 20 chars): %API_KEY:~0,20%...
echo.

echo Method 1: Bearer Authentication
curl -s -X GET "https://api.instantly.ai/api/v1/campaign/list" ^
  -H "Authorization: Bearer %API_KEY%" ^
  -H "Content-Type: application/json" ^
  -w "\nHTTP Status: %%{http_code}\n" ^
  -o "temp_response1.json"

echo.
echo Response:
type temp_response1.json
echo.
echo ================================
echo.

echo Method 2: API Key Header
curl -s -X GET "https://api.instantly.ai/api/v1/campaign/list" ^
  -H "X-API-Key: %API_KEY%" ^
  -H "Content-Type: application/json" ^
  -w "\nHTTP Status: %%{http_code}\n" ^
  -o "temp_response2.json"

echo.
echo Response:
type temp_response2.json
echo.
echo ================================
echo.

echo Method 3: Try different endpoint (account info)
curl -s -X GET "https://api.instantly.ai/api/v1/account" ^
  -H "Authorization: Bearer %API_KEY%" ^
  -H "Content-Type: application/json" ^
  -w "\nHTTP Status: %%{http_code}\n" ^
  -o "temp_response3.json"

echo.
echo Response:
type temp_response3.json
echo.

echo.
echo === Test Complete ===
echo Temporary files created: temp_response1.json, temp_response2.json, temp_response3.json
echo.

pause