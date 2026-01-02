/**
 * activity-advisor Tools Capability
 */

import * as z from 'zod';
import type {
  ListToolsRequest,
  ListToolsResult,
  CallToolRequest,
  CallToolResult,
  Tool,
} from 'wasmcp:mcp-v20250618/mcp@0.1.7';
import type { RequestCtx } from 'wasmcp:mcp-v20250618/tools@0.1.7';

// 2. Tool Discovery Handler
function listTools(
  _ctx: RequestCtx,
  _request: ListToolsRequest
): ListToolsResult {
  const tools: Tool[] = [
    {
      name: "get_activity_recommendation",
      description: "Suggest activities based on weather condition and temperature.",
      inputSchema: JSON.stringify({
        type: "object",
        properties: {
          condition: {
            type: "string",
            description: "The current weather condition (e.g., Rain, Sunny, Cloud, Snow)"
          },
          temp: {
            type: "number",
            description: "Current temperature in Celsius"
          }
        },
        required: ["condition", "temp"]
      })
    }
  ];

  return { tools };
}

// 3. Tool Execution Handler
async function callTool(
  _ctx: RequestCtx,
  request: CallToolRequest
): Promise<CallToolResult | undefined> {

  if (request.name === "get_activity_recommendation") {
    try {
      const args = JSON.parse(request.arguments || "{}");
      const condition = (args.condition || "").toLowerCase();
      const temp = args.temp;

      if (temp === undefined) {
        return errorResult("Missing required parameter: temp");
      }

      let recommendation = "";

      if (condition.includes("rain") || condition.includes("storm")) {
        recommendation = "It is raining! I recommend visiting the Visvesvaraya Museum or a cozy indoor cafe.";
      } else if (temp > 30) {
        recommendation = "It is quite hot. Stay hydrated and perhaps visit a water park or an air-conditioned mall.";
      } else if (temp < 10) {
        recommendation = "Brrr! It is cold. A good day for a hot chocolate or visiting an indoor hot spring if available.";
      } else {
        recommendation = "The weather is pleasant! Perfect for a walk in the park, a city tour, or an outdoor market.";
      }

      return textResult(recommendation);

    } catch (err) {
      return errorResult(`Failed to process request: ${err}`);
    }
  }

  return undefined; // Tool not found
}

// --- Helper Functions (Provided by Template) ---

function textResult(text: string): CallToolResult {
  return {
    content: [{
      tag: 'text',
      val: {
        text: { tag: 'text', val: text },
      },
    }],
    isError: false,
  };
}

function errorResult(message: string): CallToolResult {
  return {
    content: [{
      tag: 'text',
      val: {
        text: { tag: 'text', val: message },
      },
    }],
    isError: true,
  };
}

export const tools = {
  listTools,
  callTool,
};