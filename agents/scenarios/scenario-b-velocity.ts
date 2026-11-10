import { runSubscriptionAgent } from '../src/subscription-agent.js';

async function sleep(ms: number) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function main() {
  const totalIterations = parseInt(process.env.SCENARIO_B_ITERATIONS || '3', 10);

  console.log(`\n` + '='.repeat(72));
  console.log(`⚡ DEMO SCENARIO B: Runaway Duplicate Subscription Loop`);
  console.log('='.repeat(72));
  console.log(`A misconfigured subscription agent encounters a sync bug and triggers`);
  console.log(`a runaway loop of repeated $29.00 license renewals for Slack.`);
  console.log(`Demonstrating ${totalIterations} rapid iterations...\n`);

  for (let i = 1; i <= totalIterations; i++) {
    console.log(`\n` + '-'.repeat(72));
    console.log(`🔄 Loop Iteration ${i} of ${totalIterations}: Automated Renewal Request`);
    console.log('-'.repeat(72));

    try {
      const res = await runSubscriptionAgent(
        `Automated hourly billing sync retry cycle #${i}`,
        {
          item: `Automated Slack Seat Renewal (Burst #${i})`,
          merchantId: 'merch_saas_01',
          merchantName: 'Slack Technologies',
          merchantCategory: 'saas',
          amount: 29.00,
          justification: `Scheduled recurring license sync #${i}`
        }
      );

      console.log(`\nIteration ${i} Result: Status = ${res.status}, Decision = ${res.decision}`);
      if (res.decision === 'HOLD') {
        console.log(`\n🛑 VELOCITY BURST INTERCEPTED!`);
        console.log(`   TrustRail detected excessive transaction frequency and held iteration #${i}!`);
        if (res.shap_explanation?.features) {
          console.log(`   Key Trigger: ${res.shap_explanation.features[0]?.english}`);
        }
      } else if (res.status === 'AUTO_CAPTURED') {
        console.log(`   Normal baseline transaction cleared and auto-captured.`);
      }
    } catch (err: any) {
      console.error(`\n❌ Iteration ${i} failed:`, err.response?.data || err.message || err);
      process.exit(1);
    }

    if (i < totalIterations) {
      console.log(`\nWaiting 1 second before next burst iteration...`);
      await sleep(1000);
    }
  }

  console.log('\n' + '='.repeat(72));
  console.log('🏁 SCENARIO B FINISHED');
  console.log('='.repeat(72) + '\n');
}

main();
