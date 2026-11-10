import { paypalAgentClient } from './common/paypal-client.js';
import { agentLLM } from './common/llm-client.js';
import { AgentPurchaseRequest } from './common/types.js';
import { promptPayerApproval } from './common/approval-prompt.js';

export async function runTravelAgent(customPrompt?: string, overridePurchase?: Partial<AgentPurchaseRequest>) {
  const agentId = 'travel-agent';
  console.log(`\n========================================`);
  console.log(`🤖 Starting Travel Booking Agent`);
  console.log(`========================================`);

  const prompt = customPrompt || 'Book round-trip flight from SFO to JFK for regional customer onsite meeting.';

  const defaultPurchase: AgentPurchaseRequest = {
    item: 'Round-trip economy flight booking',
    merchantId: 'merch_trav_01',
    merchantName: 'Delta Air Lines',
    merchantCategory: 'airline',
    amount: 345.00,
    justification: 'Quarterly strategic client review travel'
  };

  const decision = await agentLLM.decidePurchase('Travel Booking Agent', prompt, defaultPurchase);
  const finalPurchase = { ...decision, ...overridePurchase };

  console.log(`✈️ Travel Reservation:`, JSON.stringify(finalPurchase, null, 2));
  console.log(`💳 Initiating PayPal Sandbox Order (intent=AUTHORIZE)...`);

  const order = await paypalAgentClient.createAuthorizeOrder(
    finalPurchase.amount,
    `${finalPurchase.item} - ${finalPurchase.justification}`
  );
  console.log(`✅ Order created: ${order.id}`);

  // Manual browser approval prompt
  await promptPayerApproval(order, finalPurchase.amount, finalPurchase.item);

  console.log(`🔐 Authorizing PayPal Order...`);
  const authId = await paypalAgentClient.authorizeOrder(order.id);
  console.log(`🔒 Authorization acquired: ${authId}`);

  console.log(`🛡️  Routing to TrustRail firewall...`);
  const result = await paypalAgentClient.submitForGovernance({
    paypal_order_id: order.id,
    paypal_auth_id: authId,
    agent_id: agentId,
    merchant_id: finalPurchase.merchantId,
    merchant_name: finalPurchase.merchantName,
    merchant_category: finalPurchase.merchantCategory,
    amount: finalPurchase.amount,
    currency: 'USD',
    description: finalPurchase.item
  });

  console.log(`\n🚦 TrustRail Governance Result:`);
  console.log(`- Transaction ID: ${result.id}`);
  console.log(`- Status: ${result.status}`);
  console.log(`- Decision: ${result.decision}`);
  if (result.risk_score !== undefined) {
    console.log(`- Risk Score: ${(result.risk_score * 100).toFixed(1)}% (Threshold: ${((result.risk_threshold || 0) * 100).toFixed(1)}%)`);
  }
  if (result.shap_explanation?.features) {
    console.log(`\n🔍 SHAP Explanations:`);
    result.shap_explanation.features.forEach((f, i) => {
      console.log(`  ${i + 1}. ${f.english}`);
    });
    if (result.shap_explanation.counterfactual) {
      console.log(`💡 Counterfactual: ${result.shap_explanation.counterfactual}`);
    }
  }

  return result;
}

if (import.meta.url === `file://${process.argv[1]}`) {
  runTravelAgent().catch(console.error);
}

