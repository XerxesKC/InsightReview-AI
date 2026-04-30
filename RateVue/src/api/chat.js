import request from '@/utils/request';

const CHAT_API_BASE_URL = 'http://127.0.0.1:8001/api/v1';

const buildChatConfig = (headers = {}, extraConfig = {}) => ({
  baseURL: CHAT_API_BASE_URL,
  ...extraConfig,
  headers: {
    ...(extraConfig.headers || {}),
    ...headers
  }
});

const buildChatUrl = (path) => `${CHAT_API_BASE_URL}${path}`;

const readErrorText = async (response) => {
  const text = await response.text();

  if (!text) {
    return `请求失败（${response.status}）`;
  }

  try {
    const payload = JSON.parse(text);
    return payload.message || payload.detail || payload.error || text;
  } catch {
    return text;
  }
};

export const streamChatCompletion = async (data, headers = {}, options = {}) => {
  const { onChunk, onDone, signal } = options;

  const response = await fetch(buildChatUrl('/chat/completions'), {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'text/event-stream',
      ...headers
    },
    body: JSON.stringify(data),
    signal
  });

  if (!response.ok) {
    throw new Error(await readErrorText(response));
  }

  const contentType = response.headers.get('content-type') || '';

  if (contentType.includes('application/json')) {
    const payload = await response.json();
    const answer = payload.answer || payload.message?.content || '';

    if (answer) {
      onChunk?.(answer, payload);
    }

    onDone?.(payload);
    return payload;
  }

  if (!response.body) {
    throw new Error('当前浏览器不支持流式响应');
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder('utf-8');
  let buffer = '';
  let donePayload = null;

  const processEventBlock = (eventBlock) => {
    const dataLines = eventBlock
      .split(/\r?\n/)
      .filter(line => line.startsWith('data:'))
      .map(line => line.slice(5).trim())
      .filter(Boolean);

    if (!dataLines.length) {
      return;
    }

    const rawData = dataLines.join('\n');

    if (rawData === '[DONE]') {
      donePayload = donePayload || { done: true };
      return;
    }

    let payload = null;

    try {
      payload = JSON.parse(rawData);
    } catch {
      return;
    }

    if (payload.done) {
      donePayload = payload;
      onDone?.(payload);
      return;
    }

    if (typeof payload.content === 'string') {
      onChunk?.(payload.content, payload);
    }
  };

  while (true) {
    const { value, done } = await reader.read();
    buffer += decoder.decode(value || new Uint8Array(), { stream: !done });

    const eventBlocks = buffer.split(/\r?\n\r?\n/);
    buffer = eventBlocks.pop() || '';

    eventBlocks.forEach(processEventBlock);

    if (done) {
      const tail = buffer.trim();

      if (tail) {
        processEventBlock(tail);
      }

      break;
    }
  }

  return donePayload;
};

export const uploadChatImage = (file, headers = {}, onUploadProgress) => {
  const formData = new FormData();
  formData.append('file', file);

  return request.post('/chat/images/upload', formData, {
    ...buildChatConfig(headers),
    headers: {
      'Content-Type': 'multipart/form-data',
      ...headers
    },
    onUploadProgress
  });
};

export const getChatImageBlob = (imageId, headers = {}) => request({
  url: `/chat/images/${encodeURIComponent(imageId)}`,
  method: 'get',
  responseType: 'blob',
  ...buildChatConfig(headers)
});

export const getChatSessions = (params = {}, headers = {}) => request({
  url: '/chat/sessions',
  method: 'get',
  params,
  ...buildChatConfig(headers)
});

export const getChatSessionHistory = (sessionId, params = {}, headers = {}) => request({
  url: `/chat/sessions/${encodeURIComponent(sessionId)}/history`,
  method: 'get',
  params,
  ...buildChatConfig(headers)
});

export const getChatSessionRetrievalConfig = (sessionId, headers = {}) => request({
  url: `/chat/sessions/${encodeURIComponent(sessionId)}/retrieval-config`,
  method: 'get',
  ...buildChatConfig(headers)
});

export const updateChatSessionRetrievalConfig = (sessionId, data, headers = {}) => request({
  url: `/chat/sessions/${encodeURIComponent(sessionId)}/retrieval-config`,
  method: 'put',
  data,
  ...buildChatConfig(headers)
});

export const updateChatSessionTitle = (sessionId, data, headers = {}) => request({
  url: `/chat/sessions/${encodeURIComponent(sessionId)}`,
  method: 'patch',
  data,
  ...buildChatConfig(headers)
});

export const updateChatTurnRating = (data, headers = {}) => request({
  url: '/chat/turn/rating',
  method: 'put',
  data,
  ...buildChatConfig(headers)
});

export const clearChatSessionContext = (sessionId, headers = {}) => request({
  url: `/chat/sessions/${encodeURIComponent(sessionId)}/context`,
  method: 'delete',
  ...buildChatConfig(headers)
});

export const rollbackChatSession = (sessionId, data, headers = {}) => request({
  url: `/chat/sessions/${encodeURIComponent(sessionId)}/rollback`,
  method: 'post',
  data,
  ...buildChatConfig(headers)
});

export const deleteChatSession = (sessionId, headers = {}) => request({
  url: `/chat/sessions/${encodeURIComponent(sessionId)}`,
  method: 'delete',
  ...buildChatConfig(headers)
});

export const uploadChatFile = (file, headers = {}, onUploadProgress) => {
  const formData = new FormData();
  formData.append('file', file);

  return request.post('/chat/files/upload', formData, {
    ...buildChatConfig(headers),
    headers: {
      'Content-Type': 'multipart/form-data',
      ...headers
    },
    onUploadProgress
  });
};
