#!/usr/bin/env bash
set -e

echo "=========================================================="
echo "   TrustRail — Scripted End-to-End Demo Sequence          "
echo "=========================================================="
echo "Ensure Backend (http://127.0.0.1:8000) and Dashboard (http://localhost:5173) are running."
echo "Note: Each scenario prints a PayPal Sandbox checkout URL — log in as your US Personal sandbox buyer, click 'Pay Now', then press Enter in the terminal."

echo -e "\n>>> [SCENARIO A] Running Prompt-Injection Rogue Purchase Attack..."
cd agents && npx tsx scenarios/scenario-a-rogue.ts && cd ..

echo -e "\n[Verify Dashboard] Notice VOIDED status (POLICY_BLOCK), real ~100% ML Risk Score, SHAP drivers, and Procurement Agent Trust penalty."
read -p "Press Enter to proceed to Scenario B..."

echo -e "\n>>> [SCENARIO B] Running Runaway Duplicate Subscription Loop..."
cd agents && npx tsx scenarios/scenario-b-velocity.ts && cd ..

echo -e "\n[Verify Dashboard] Notice Iteration 1 AUTO_CAPTURED, velocity trust freeze during burst, and HELD interception triggered by same_merchant_txn_1h."
read -p "Press Enter to proceed to Scenario C..."

echo -e "\n>>> [SCENARIO C] Running Legitimate Large One-Off Purchase..."
cd agents && npx tsx scenarios/scenario-c-legitimate.ts && cd ..

echo -e "\n[Action Required] Open http://localhost:5173, locate the HELD \$2,800 Delta Air Lines flight, review SHAP explanations,"
echo "and click 'Approve & Capture'. Observe status flip to CAPTURED on PayPal Sandbox and Travel Booking Agent Trust Score increase!"
echo -e "\nDemo run complete!"
