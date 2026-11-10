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
    const geminiKey = process.env.GEMINI_API_KEY?.trim();
    const openaiKey = process.env.OPENAI_API_KEY?.trim();
    const isValidKey = (k?: string) =>
      !!k && !k.includes('placeholder') && !k.includes('your_llm') && !k.includes('your_gemini');

    if (isValidKey(geminiKey)) {
      this.model = process.env.LLM_MODEL || 'gemini-2.5-flash';
      this.openai = new OpenAI({
        apiKey: geminiKey,
        baseURL: process.env.LLM_BASE_URL || 'https://generativelanguage.googleapis.com/v1beta/openai/',
      });
    } else if (isValidKey(openaiKey)) {
      this.model = process.env.LLM_MODEL || 'gpt-4o-mini';
      this.openai = new OpenAI({
        apiKey: openaiKey,
        ...(process.env.LLM_BASE_URL ? { baseURL: process.env.LLM_BASE_URL } : {}),
      });
    } else {
      this.model = process.env.LLM_MODEL || 'gemini-2.5-flash';
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

