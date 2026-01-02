/**
 * weather-tool Tools Capability
 *
 * A tools capability that provides example operations.
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

declare var fetch: any;


const GetWeatherSchema = z.object({
  city: z.string().describe('City to get weather for'),
});

type GetWeatherArgs = z.infer<typeof GetWeatherSchema>;

function listTools(
  _ctx: RequestCtx,
  _request: ListToolsRequest
): ListToolsResult {
  const tools: Tool[] = [
    {
      name: 'get_weather',
      inputSchema: JSON.stringify(z.toJSONSchema(GetWeatherSchema)),
      options: {
        title: 'Get Weather',
        description: 'Get current temperature for a given city',
      },
    },
  ];

  return { tools };
}

async function callTool(
  _ctx: RequestCtx,
  request: CallToolRequest
): Promise<CallToolResult | undefined> {
  switch (request.name) {
    case 'get_weather':
      return await handleGetWeather(request.arguments);
    default:
      return undefined; // We don't handle this tool
  }
}


async function handleGetWeather(args?: string): Promise<CallToolResult> {
  try {
    if (!args) {
      return errorResult('Arguments are required');
    }

    const parsed: GetWeatherArgs = GetWeatherSchema.parse(JSON.parse(args));
    const city = parsed.city;

    // 1. Geocoding: City Name -> Lat/Long
    const geoRes = await fetch(`https://geocoding-api.open-meteo.com/v1/search?name=${city}&count=1`);
    const geoData = await geoRes.json() as any;

    if (!geoData.results) return errorResult(`City ${city} not found.`);
    const { latitude, longitude, name } = geoData.results[0];

    // 2. Weather: Lat/Long -> Temperature
    const weatherRes = await fetch(`https://api.open-meteo.com/v1/forecast?latitude=${latitude}&longitude=${longitude}&current_weather=true`);
    const weatherData = await weatherRes.json() as any;

    const temp = weatherData.current_weather.temperature;
    return textResult(`The current temperature in ${name} is ${temp}°C.`);

  } catch (error: any) {
    if (error instanceof z.ZodError) {
      return errorResult(`Invalid arguments: ${error.message}`);
    }
    return errorResult(
      `Error fetching weather: ${error instanceof Error ? error.message : String(error)}`
    );
  }
}

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
