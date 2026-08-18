
const BASE_URL = process.env.REACT_APP_API_URL || "http://localhost:8000";

async function handleResponse(res) {
  if (!res.ok) {
    let detail = `Errore HTTP ${res.status}`;
    try {
      const errBody = await res.json();
      detail = errBody?.detail || detail;
    } catch {
      // corpo non JSON
    }
    throw new Error(detail);
  }
  return res.json();
}

export async function analyzeImage(imageFile, model) {
  const formData = new FormData();
  formData.append("file", imageFile);
  if (model) formData.append("model", model);

  const res = await fetch(`${BASE_URL}/analyze`, {
    method: "POST",
    body: formData,
  });
  return handleResponse(res);
}

export async function evaluateAnswer({ question, correctAnswer, userAnswer, model }) {
  const res = await fetch(`${BASE_URL}/evaluate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      question,
      correctAnswer,
      userAnswer,
      ...(model ? { model } : {}),
    }),
  });
  return handleResponse(res);
}

export async function checkHealth() {
  const res = await fetch(`${BASE_URL}/health`);
  return handleResponse(res);
}
