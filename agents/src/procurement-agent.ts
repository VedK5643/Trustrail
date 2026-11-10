import { paypalAgentClient } from './common/paypal-client.js';
import { agentLLM } from './common/llm-client.js';
import { AgentPurchaseRequest } from './common/types.js';
import { promptPayerApproval } from './common/approval-prompt.js';

export async function runProcurementAgent(customPrompt?: string, overridePurchase?: Partial<AgentPurchaseRequest>) {
  const agentId = 'procurement-agent';
  console.log(`\n========================================`);
  console.log(`🤖 Starting Procurement Agent`);
  console.log(`========================================`);

  const prompt = customPrompt || 'Restock 5 boxes of multi-purpose copy paper and ergonomic wrist rests for the 4th floor engineering bay.';
  
  const defaultPurchase: AgentPurchaseRequest = {
    item: 'Bulk copy paper & ergonomic office accessories',
    merchantId: 'merch_off_01',
    merchantName: 'Staples Business',
    merchantCategory: 'office_supplies',
    amount: 88.50,
    justification: 'Weekly engineering supply replenishment'
  };

  const decision = await agentLLM.decidePurchase('Procurement Agent', prompt, defaultPurchase);
  const finalPurchase = { ...decision, ...overridePurchase };

  console.log(`📦 Procurement Decision:`, JSON.stringify(finalPurchase, null, 2));
  console.log(`💳 Initiating PayPal Sandbox Order with intent=AUTHORIZE...`);

  const order = await paypalAgentClient.createAuthorizeOrder(
    finalPurchase.amount,
    `${finalPurchase.item} - ${finalPurchase.justification}`
  );
  console.log(`✅ Order created: ${order.id} (Status: ${order.status})`);

  // Manual browser approval prompt
  await promptPayerApproval(order, finalPurchase.amount, finalPurchase.item);

  console.log(`🔐 Authorizing PayPal Order funds...`);
  const authId = await paypalAgentClient.authorizeOrder(order.id);
  console.log(`🔒 Authorization acquired: ${authId}`);

  console.log(`🛡️  Routing to TrustRail spend-governance firewall...`);
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
  if (result.decision_reason) {
    console.log(`- Reason: ${result.decision_reason}`);
  }
  if (result.shap_explanation?.features) {
    console.log(`\n🔍 SHAP Top Contributing Explanations:`);
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
  runProcurementAgent().catch(console.error);
}

