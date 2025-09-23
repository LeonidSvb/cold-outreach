# Apollo API Test для сбора лидов маркетинговых агентств
# PowerShell скрипт для тестирования API

$apiKey = "vSJb2-hxp_tbdxy7K8tvgw"
$baseUrl = "https://api.apollo.io/v1"

# Headers для Apollo API
$headers = @{
    "Content-Type" = "application/json"
    "Cache-Control" = "no-cache"
    "X-Api-Key" = $apiKey
}

# Параметры поиска маркетинговых агентств
$searchParams = @{
    "page" = 1
    "per_page" = 10
    "organization_locations" = @("United States")
    "organization_num_employees_ranges" = @("11,50")
    "organization_industry_tag_ids" = @(
        "5567cdfc74636479ba000015",  # Marketing Services
        "5567cdfc74636479ba000016"   # Advertising
    )
    "organization_keywords" = @(
        "lead generation",
        "digital marketing", 
        "PPC agency",
        "marketing automation"
    )
    "organization_technologies" = @(
        "HubSpot",
        "Salesforce",
        "Google Ads"
    )
    "organization_founded_year_min" = 2015
    "organization_founded_year_max" = 2022
    "prospected_by_current_team" = @("no")
} | ConvertTo-Json -Depth 3

Write-Host "🚀 Тестируем Apollo API для поиска маркетинговых агентств..." -ForegroundColor Green

try {
    $response = Invoke-RestMethod -Uri "$baseUrl/mixed_people/search" -Method POST -Headers $headers -Body $searchParams
    
    Write-Host "✅ Успешный ответ от Apollo API!" -ForegroundColor Green
    Write-Host "Найдено организаций: $($response.organizations.Count)" -ForegroundColor Yellow
    
    # Создаем CSV файл с результатами
    $csvData = @()
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    
    foreach ($org in $response.organizations) {
        # Простой скоринг
        $score = 50  # Базовый балл
        
        # Бонус за размер команды
        if ($org.estimated_num_employees -ge 25) { $score += 15 }
        elseif ($org.estimated_num_employees -ge 10) { $score += 10 }
        
        # Бонус за технологии
        if ($org.technologies) { $score += 10 }
        
        # Бонус за LinkedIn и website
        if ($org.linkedin_url -and $org.website_url) { $score += 15 }
        
        # Бонус за открытые позиции
        if ($org.num_current_positions -gt 0) { $score += 10 }
        
        $csvRow = [PSCustomObject]@{
            "Company_Name" = $org.name
            "Domain" = ($org.website_url -replace "https?://", "")
            "Website_URL" = $org.website_url
            "LinkedIn_URL" = $org.linkedin_url
            "Industry" = $org.industry
            "Employee_Count" = $org.estimated_num_employees
            "Location_City" = $org.primary_location.city
            "Location_State" = $org.primary_location.state
            "Location_Country" = $org.primary_location.country
            "Founded_Year" = $org.founded_year
            "Technologies" = ($org.technologies.name -join ", ")
            "Job_Openings" = $org.num_current_positions
            "Lead_Score" = $score
            "Collection_Date" = (Get-Date -Format "yyyy-MM-dd")
            "Enrichment_Priority" = if ($score -ge 70) { "High" } else { "Medium" }
            "Target_Persona" = "Agency Owner/CMO"
        }
        
        $csvData += $csvRow
    }
    
    # Фильтруем только качественные лиды (70+ баллов)
    $qualityLeads = $csvData | Where-Object { $_.Lead_Score -ge 70 }
    
    # Экспортируем в CSV
    $csvFileName = "marketing_agencies_leads_$timestamp.csv"
    $csvPath = "C:\Users\79818\Desktop\Outreach - new\$csvFileName"
    $csvData | Export-Csv -Path $csvPath -NoTypeInformation -Encoding UTF8
    
    Write-Host "💾 Данные экспортированы в: $csvFileName" -ForegroundColor Cyan
    Write-Host "📊 Общее количество компаний: $($csvData.Count)" -ForegroundColor Yellow
    Write-Host "⭐ Качественных лидов (70+ баллов): $($qualityLeads.Count)" -ForegroundColor Green
    
    # Выводим топ лиды
    Write-Host "`n🏆 ТОП КАЧЕСТВЕННЫЕ ЛИДЫ:" -ForegroundColor Magenta
    $qualityLeads | Sort-Object Lead_Score -Descending | Select-Object -First 5 | ForEach-Object {
        Write-Host "• $($_.Company_Name) - Score: $($_.Lead_Score) - $($_.Location_City), $($_.Location_State)" -ForegroundColor White
    }
    
} catch {
    Write-Host "❌ Ошибка при обращении к Apollo API: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n✅ Тест завершен!" -ForegroundColor Green