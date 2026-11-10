import readline from 'readline';
import { PayPalOrderResponse } from './types.js';

/**
 * Prompts the developer in terminal to open the PayPal Sandbox approval URL,
 * log in as the sandbox buyer, approve the authorization, and press Enter to continue.
 */
export async function promptPayerApproval(
  order: PayPalOrderResponse,
  amount: number,
  description: string
): Promise<void> {
  const buyerEmail = process.env.PAYPAL_SANDBOX_BUYER_EMAIL || 'sb-buyer@personal.example.com';
  const approveLink =
    order.links?.find((l) => l.rel === 'payer-action' || l.rel === 'approve')?.href ||
    `https://www.sandbox.paypal.com/checkoutnow?token=${order.id}`;

  console.log('\n' + '='.repeat(72));
  console.log('  ⚠️  ACTION REQUIRED: APPROVE ORDER IN PAYPAL SANDBOX');
  console.log('='.repeat(72));
  console.log(`  Order ID    : ${order.id}`);
  console.log(`  Amount      : $${amount.toFixed(2)} USD`);
  console.log(`  Description : ${description}`);
  console.log(`\n  👉 1. Open this link in your browser:`);
  console.log(`     \x1b[36m${approveLink}\x1b[0m`);
  console.log(`\n  👉 2. Log in with your Sandbox Buyer account:`);
  console.log(`     Email: ${buyerEmail}`);
  console.log(`\n  👉 3. Click "Pay Now" / "Complete Purchase" to approve the authorization.`);
  console.log('='.repeat(72));

  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout,
  });

  return new Promise((resolve) => {
    rl.question('\n  Press [Enter] AFTER completing approval in your browser... ', () => {
      rl.close();
      console.log('  Continuing to authorize order funds...\n');
      resolve();
    });
  });
}

