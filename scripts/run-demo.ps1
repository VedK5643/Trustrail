Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "   TrustRail — Scripted End-to-End Demo Sequence          " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "Ensure Backend (http://127.0.0.1:8000) and Dashboard (http://localhost:5173) are running." -ForegroundColor Yellow
Write-Host "Note: Each scenario prints a PayPal Sandbox checkout URL — log in as your US Personal sandbox buyer, click 'Pay Now', then press Enter in the terminal.`n" -ForegroundColor Cyan

# Scenario A: Rogue purchase
Write-Host "`n>>> [SCENARIO A] Running Prompt-Injection Rogue Purchase Attack..." -ForegroundColor Magenta
Set-Location agents
npx tsx scenarios/scenario-a-rogue.ts
Set-Location ..

Write-Host "`n[Verify Dashboard] Notice VOIDED status (POLICY_BLOCK), real ~100% ML Risk Score, SHAP drivers, and Procurement Agent Trust penalty." -ForegroundColor Yellow
Read-Host -Prompt "Press Enter to proceed to Scenario B..."

# Scenario B: Velocity loop
Write-Host "`n>>> [SCENARIO B] Running Runaway Duplicate Subscription Loop..." -ForegroundColor Magenta
Set-Location agents
npx tsx scenarios/scenario-b-velocity.ts
Set-Location ..

Write-Host "`n[Verify Dashboard] Notice Iteration 1 AUTO_CAPTURED, velocity trust freeze during burst, and HELD interception triggered by same_merchant_txn_1h." -ForegroundColor Yellow
Read-Host -Prompt "Press Enter to proceed to Scenario C..."

# Scenario C: Legitimate large purchase
Write-Host "`n>>> [SCENARIO C] Running Legitimate Large One-Off Purchase..." -ForegroundColor Magenta
Set-Location agents
npx tsx scenarios/scenario-c-legitimate.ts
Set-Location ..

Write-Host "`n[Action Required] Open http://localhost:5173, locate the HELD $2,800 Delta Air Lines flight, review SHAP explanations," -ForegroundColor Yellow
Write-Host "and click 'Approve & Capture'. Observe status flip to CAPTURED on PayPal Sandbox and Travel Booking Agent Trust Score increase!" -ForegroundColor Green
Write-Host "`nDemo run complete!" -ForegroundColor Cyan
