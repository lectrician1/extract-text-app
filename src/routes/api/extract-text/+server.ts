import { json } from '@sveltejs/kit';
import fetch from 'node-fetch';
import { config } from 'dotenv';

config();

const AZURE_COMPUTER_VISION_SUBSCRIPTION_KEY = process.env.AZURE_COMPUTER_VISION_SUBSCRIPTION_KEY;
const AZURE_COMPUTER_VISION_ENDPOINT = process.env.AZURE_COMPUTER_VISION_ENDPOINT;

export const POST = async ({ request }) => {
    const { imageData } = await request.json();

    const buffer = Buffer.from(imageData, 'base64');

    const analyzeUrl = `${AZURE_COMPUTER_VISION_ENDPOINT}/vision/v3.2/read/analyze`;

    const response = await fetch(analyzeUrl, {
        method: 'POST',
        headers: {
            'Ocp-Apim-Subscription-Key': AZURE_COMPUTER_VISION_SUBSCRIPTION_KEY,
            'Content-Type': 'application/octet-stream'
        },
        body: buffer
    });

    const operationLocation = response.headers.get('Operation-Location');

    let result = {};
    let status = 'running';
    while (status === 'running' || status === 'notStarted') {
        const resultResponse = await fetch(operationLocation, {
            headers: { 'Ocp-Apim-Subscription-Key': AZURE_COMPUTER_VISION_SUBSCRIPTION_KEY }
        });
        result = await resultResponse.json();
        status = result.status;
        if (status === 'running' || status === 'notStarted') {
            await new Promise(res => setTimeout(res, 1000));
        }
    }

    return json(result);
};
