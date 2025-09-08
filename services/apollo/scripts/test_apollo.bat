@echo off
echo Тестируем Apollo API...

curl -X POST "https://api.apollo.io/v1/mixed_companies/search" ^
-H "Cache-Control: no-cache" ^
-H "Content-Type: application/json" ^
-H "X-Api-Key: vSJb2-hxp_tbdxy7K8tvgw" ^
-d "{\"q_organization_name\": \"tesla\", \"page\": 1, \"per_page\": 3}"

echo.
echo Тест завершен.
pause