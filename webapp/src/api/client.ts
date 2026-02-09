export async function postRequest(formData: FormData): Promise<{ok: boolean; request_id: number}> {
  const res = await fetch('/api/requests', { method: 'POST', body: formData });
  if (!res.ok) throw new Error('Failed to create request');
  return res.json();
}
