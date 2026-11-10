/**
 * STRETCH FEATURE (Not wired into the core Scenario A/B/C demo flow).
 * Demonstrates feeding PayPal Customer Disputes outcomes back into TrustRail's
 * Beta-distribution trust engine; falls back to sample ID 'PP-D-10293' if no live
 * sandbox disputes exist on the merchant account.
 */
import axios from 'axios';
import dotenv from 'dotenv';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
dotenv.config({ path: path.resolve(__dirname, '../../.env') });

const backendUrl = process.env.BACKEND_URL || 'http://localhost:8000';

async function main() {
  console.log(`\n===============================================================`);
  console.log(`⚖️  DEMO SCENARIO D (Stretch): PayPal Customer Disputes Ground Truth`);
  console.log(`===============================================================`);

  console.log(`Fetching active disputes from PayPal Customer Disputes API...`);
  try {
    const listRes = await axios.get(`${backendUrl}/disputes`);
    console.log(`Disputes retrieved from PayPal:`, JSON.stringify(listRes.data, null, 2));

    const disputeId = listRes.data.items?.[0]?.dispute_id || 'PP-D-10293';
    const targetAgent = 'procurement-agent';

    console.log(`\nSimulating Dispute Resolution event from PayPal:`);
    console.log(`- Dispute ID: ${disputeId}`);
    console.log(`- Agent implicated: ${targetAgent}`);
    console.log(`- Outcome: RESOLVED_BUYER_FAVOUR (Customer won dispute for non-delivery)`);

    const resolveRes = await axios.post(`${backendUrl}/disputes/${disputeId}/resolve`, {
      agent_id: targetAgent,
      outcome: 'RESOLVED_BUYER_FAVOUR',
      note: 'Item never arrived at engineering dock, buyer refund granted'
    });

    console.log(`\n🚦 TrustRail Ground Truth Update:`);
    console.log(`- Message: ${resolveRes.data.message}`);
    console.log(`- Updated Trust Score: ${(resolveRes.data.new_trust_score * 100).toFixed(1)}%`);
    console.log(`- Beta Parameters: α = ${resolveRes.data.trust_alpha}, β = ${resolveRes.data.trust_beta} (+3.0 penalty applied)`);
  } catch (err: any) {
    console.error('Scenario D error:', err.response?.data || err.message);
  }
}

main();

