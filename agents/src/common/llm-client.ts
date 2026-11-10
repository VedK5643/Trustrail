import OpenAI from 'openai';
import dotenv from 'dotenv';
import path from 'path';
import { fileURLToPath } from 'url';
import { AgentPurchaseRequest } from './types.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
dotenv.config({ path: path.resolve(__dirname, '../../../.env') });

export class AgentLLMClient {
  private openai: OpenAI | null = null;
  private model: string;

  constructor() {
    const apiKey = process.env.OPENAI_API_KEY;
    this.model = process.env.LLM_MODEL || 'gpt-4o-mini';

    if (apiKey && !apiKey.includes('placeholder') && !apiKey.includes('your_llm')) {
      this.openai = new OpenAI({ apiKey });
    }
  }

  async decidePurchase(agentRole: string, prompt: string, defaultPurchase: AgentPurchaseRequest): Promise<AgentPurchaseRequest> {
    if (!this.openai) {
      console.log(`[${agentRole}] Using deterministic agent reasoning for instruction: "${prompt}"`);
      return defaultPurchase;
    }

    try {
      const response = await this.openai.chat.completions.create({
        model: this.model,
        messages: [
          {
            role: 'system',
            content: `You are an autonomous enterprise AI agent in the role of: ${agentRole}.
Based on incoming user instructions or work tasks, formulate a purchase request.
Respond with ONLY valid JSON with keys: item, merchantId, merchantName, merchantCategory, amount, justification.`
          },
          {
            role: 'user',
            content: prompt
          }
        ],
        response_format: { type: 'json_object' },
        temperature: 0.2
      });

      const content = response.choices[0]?.message?.content;
      if (content) {
        return JSON.parse(content) as AgentPurchaseRequest;
      }
    } catch (err) {
      console.warn(`[${agentRole}] LLM call error, using structured fallback:`, err);
    }

    return defaultPurchase;
  }
}

export const agentLLM = new AgentLLMClient();

