import { runTravelAgent } from '../src/travel-agent.js';

async function main() {
  console.log(`\n` + '='.repeat(72));
  console.log(`✈️  DEMO SCENARIO C: Legitimate Large One-Off Corporate Purchase`);
  console.log('='.repeat(72));
  console.log(`The Travel Booking Agent reserves an executive transatlantic flight`);
  console.log(`for $2,800.00 to SFO -> LHR on Delta Air Lines.`);
  console.log(`This is legitimate business travel, but 8x above the agent's $355 average.`);
  console.log(`TrustRail should place this on HOLD for human review rather than auto-capturing.\n`);

  const prompt = 'Book executive business-class transatlantic flight from SFO to LHR for VP of Engineering strategic client summit.';

  const purchase = {
    item: 'Executive Business Class Transatlantic Flight (SFO -> LHR)',
    merchantId: 'merch_trav_01',
    merchantName: 'Delta Air Lines',
    merchantCategory: 'airline',
    amount: 2800.00,
    justification: 'VP Engineering International Summit Travel'
  };

  try {
    const res = await runTravelAgent(prompt, purchase);

    console.log('\n' + '='.repeat(72));
    console.log('🏁 SCENARIO C OUTCOME SUMMARY:');
    console.log('='.repeat(72));
    console.log(`- Transaction ID : ${res.id}`);
    console.log(`- Order ID       : ${res.paypal_order_id}`);
    console.log(`- Auth ID        : ${res.paypal_auth_id}`);
    console.log(`- Status         : ${res.status}`);
    console.log(`- Decision       : ${res.decision}`);
    if (res.risk_score !== undefined) {
      console.log(`- Risk Score     : ${(res.risk_score * 100).toFixed(1)}% (Threshold: ${((res.risk_threshold || 0) * 100).toFixed(1)}%)`);
    }

    if (res.shap_explanation?.features) {
      console.log(`\n🔍 SHAP Top Contributing Explanations:`);
      res.shap_explanation.features.forEach((f, i) => {
        console.log(`   ${i + 1}. ${f.english}`);
      });
      if (res.shap_explanation.counterfactual) {
        console.log(`\n💡 Counterfactual Insight:`);
        console.log(`   ${res.shap_explanation.counterfactual}`);
      }
    }

    console.log('\n' + '-'.repeat(72));
    console.log(`👉 DEMO STEP: HUMAN-IN-THE-LOOP APPROVAL`);
    console.log('-'.repeat(72));
    console.log(`1. Open the TrustRail Dashboard at: http://localhost:5173`);
    console.log(`2. Locate the HELD transaction (${res.id}) in the Live Transaction Feed.`);
    console.log(`3. Review the SHAP explanation card and click the "Approve" button.`);
    console.log(`4. Observe TrustRail call PayPal's capture endpoint in real-time,`);
    console.log(`   changing the status to CAPTURED and increasing the agent's Trust Score!`);
    console.log('='.repeat(72) + '\n');
  } catch (err: any) {
    console.error('\n❌ Scenario C failed with error:', err.response?.data || err.message || err);
    process.exit(1);
  }
}

main();
