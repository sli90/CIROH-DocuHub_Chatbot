# API Configuration

This application integrates with a chat API. Here's how to configure it:

## Environment Variables

Create a `.env` file in the root directory with the following variable:

```env
VITE_API_BASE_URL=http://localhost:3000
```

Replace `http://localhost:3000` with your actual API endpoint. If no environment variable is set, it defaults to `http://localhost:3000`.

## API Endpoint

The application expects a POST endpoint at `/ask` that accepts the following request format:

### Request

```json
{
  "text": "Your question here"
}
```

### Response

```json
{
  "answer": "The AI response to your question",
  "sources": "Sources or references for the answer"
}
```

## Error Handling

The application includes comprehensive error handling for:

- Network connectivity issues
- Server errors (5xx)
- Client errors (4xx)
- Request timeouts
- Retry logic with exponential backoff

## Features

- **Automatic retries**: Failed requests are automatically retried up to 3 times
- **Timeout handling**: Requests timeout after 30 seconds
- **User feedback**: Clear error messages for different failure scenarios
- **Loading states**: Visual indicators while waiting for responses
- **Example questions**: All example questions now send real API requests

## Testing

To test the integration:

1. Set up your API endpoint
2. Configure the `VITE_API_BASE_URL` environment variable
3. Start the development server
4. Click on any example question or type a custom question
5. The question will be sent to your API and the response will be displayed
