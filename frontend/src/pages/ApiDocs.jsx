import React, { useState } from 'react';
import { 
  Code2, 
  Copy, 
  Check, 
  Terminal, 
  Globe, 
  Layers, 
  FileText 
} from 'lucide-react';

export default function ApiDocs() {
  const [copiedKey, setCopiedKey] = useState(null);

  const handleCopy = (text, key) => {
    navigator.clipboard.writeText(text);
    setCopiedKey(key);
    setTimeout(() => setCopiedKey(null), 2000);
  };

  const curlSingle = `curl -X POST "http://localhost:8000/api/v1/verify" \\
  -H "Content-Type: application/json" \\
  -d '{"email": "alex.doe@gmail.com"}'`;

  const pythonSingle = `import requests

url = "http://localhost:8000/api/v1/verify"
payload = {"email": "alex.doe@gmail.com"}

response = requests.post(url, json=payload)
data = response.json()

print(f"Status: {data['status']}")
print(f"Score: {data['score']}/100")
print(f"MX Configured: {data['checks']['mx']['passed']}")`;

  const jsSingle = `const response = await fetch("http://localhost:8000/api/v1/verify", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ email: "alex.doe@gmail.com" })
});

const data = await response.json();
console.log(data.status, data.score);`;

  const sampleResponse = `{
  "email": "alex.doe@gmail.com",
  "normalized_email": "alex.doe@gmail.com",
  "domain": "gmail.com",
  "status": "VALID",
  "score": 95,
  "confidence": 95,
  "confidence_level": "HIGH",
  "verification_method": "Non-delivery technical verification",
  "notification_sent": false,
  "checks": {
    "syntax": { "passed": true, "status": "PASS", "message": "Email conforms to RFC 5322 syntax standards." },
    "domain": { "passed": true, "status": "PASS", "message": "Domain 'gmail.com' format is valid." },
    "dns": { "passed": true, "status": "PASS", "message": "Domain resolved successfully (1 active IP record)." },
    "mx": { "passed": true, "status": "PASS", "message": "5 MX records configured." },
    "smtp": { "passed": true, "status": "ACCEPTED", "message": "Mailbox recipient accepted by destination mail server (250 OK)." },
    "disposable": { "passed": true, "status": "NO", "message": "Domain is not identified as a disposable inbox." },
    "role_based": { "passed": true, "status": "NO", "message": "Address is individual, not a generic role alias." }
  },
  "message": "Email address passed all technical syntax, DNS, MX, and recipient mailbox non-delivery checks.",
  "reason": "Mail server accepted recipient address (250 OK) and rejected non-existent probe."
}`;

  return (
    <div className="space-y-8 max-w-5xl">
      {/* Header */}
      <div className="pb-2 border-b border-slate-200">
        <h1 className="text-2xl font-bold text-navy-900 tracking-tight">API Reference & Integration Guide</h1>
        <p className="text-sm text-slate-600 mt-0.5">
          Integrate OpenMail Verify REST endpoints into your applications, forms, and backend pipelines.
        </p>
      </div>

      {/* Base URL info */}
      <div className="saas-card p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">Base API URL</span>
          <code className="px-2.5 py-1 bg-slate-100 rounded text-xs font-mono text-navy-900 font-bold border border-slate-200">
            http://localhost:8000/api/v1
          </code>
        </div>
        <a 
          href="http://localhost:8000/docs" 
          target="_blank" 
          rel="noreferrer"
          className="text-xs text-navy-700 font-semibold hover:underline flex items-center gap-1 self-start sm:self-auto"
        >
          Open Interactive OpenAPI (Swagger) UI &rarr;
        </a>
      </div>

      {/* Endpoint 1: Single verify */}
      <div className="saas-card p-6 space-y-6">
        <div className="flex items-center gap-3 pb-3 border-b border-slate-200">
          <span className="px-2.5 py-1 rounded bg-navy-800 text-white font-mono text-xs font-bold">POST</span>
          <span className="font-mono text-sm font-bold text-navy-900">/api/v1/verify</span>
          <span className="text-xs text-slate-500 ml-auto">Single Email Validation</span>
        </div>

        <div>
          <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-2">Request Body (JSON)</h4>
          <pre className="bg-slate-900 text-slate-100 p-3 rounded font-mono text-xs overflow-x-auto">
{`{
  "email": "alex.doe@gmail.com"
}`}
          </pre>
        </div>

        {/* Code Snippets */}
        <div className="space-y-4">
          <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-500">Integration Code Samples</h4>
          
          {/* cURL */}
          <div className="border border-slate-200 rounded overflow-hidden">
            <div className="bg-slate-50 px-3 py-1.5 border-b border-slate-200 flex items-center justify-between text-xs font-semibold text-slate-700">
              <span>cURL</span>
              <button
                onClick={() => handleCopy(curlSingle, 'curl')}
                className="text-slate-500 hover:text-navy-900 flex items-center gap-1"
              >
                {copiedKey === 'curl' ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
                {copiedKey === 'curl' ? 'Copied' : 'Copy'}
              </button>
            </div>
            <pre className="bg-slate-900 text-slate-100 p-3 font-mono text-xs overflow-x-auto">
              {curlSingle}
            </pre>
          </div>

          {/* Python */}
          <div className="border border-slate-200 rounded overflow-hidden">
            <div className="bg-slate-50 px-3 py-1.5 border-b border-slate-200 flex items-center justify-between text-xs font-semibold text-slate-700">
              <span>Python (requests)</span>
              <button
                onClick={() => handleCopy(pythonSingle, 'python')}
                className="text-slate-500 hover:text-navy-900 flex items-center gap-1"
              >
                {copiedKey === 'python' ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
                {copiedKey === 'python' ? 'Copied' : 'Copy'}
              </button>
            </div>
            <pre className="bg-slate-900 text-slate-100 p-3 font-mono text-xs overflow-x-auto">
              {pythonSingle}
            </pre>
          </div>

          {/* JavaScript */}
          <div className="border border-slate-200 rounded overflow-hidden">
            <div className="bg-slate-50 px-3 py-1.5 border-b border-slate-200 flex items-center justify-between text-xs font-semibold text-slate-700">
              <span>JavaScript (fetch)</span>
              <button
                onClick={() => handleCopy(jsSingle, 'js')}
                className="text-slate-500 hover:text-navy-900 flex items-center gap-1"
              >
                {copiedKey === 'js' ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
                {copiedKey === 'js' ? 'Copied' : 'Copy'}
              </button>
            </div>
            <pre className="bg-slate-900 text-slate-100 p-3 font-mono text-xs overflow-x-auto">
              {jsSingle}
            </pre>
          </div>
        </div>

        {/* Expected Response */}
        <div>
          <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-2">Response (200 OK)</h4>
          <pre className="bg-slate-900 text-emerald-400 p-4 rounded font-mono text-xs overflow-x-auto leading-relaxed max-h-80">
            {sampleResponse}
          </pre>
        </div>
      </div>

      {/* Endpoint 2: Batch audit */}
      <div className="saas-card p-6 space-y-4">
        <div className="flex items-center gap-3 pb-3 border-b border-slate-200">
          <span className="px-2.5 py-1 rounded bg-navy-800 text-white font-mono text-xs font-bold">POST</span>
          <span className="font-mono text-sm font-bold text-navy-900">/api/v1/verify/batch</span>
          <span className="text-xs text-slate-500 ml-auto">Batch Validation (Up to 50 emails)</span>
        </div>

        <div>
          <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-2">Request Body (JSON)</h4>
          <pre className="bg-slate-900 text-slate-100 p-3 rounded font-mono text-xs overflow-x-auto">
{`{
  "emails": [
    "user1@gmail.com",
    "support@company.org",
    "test@mailinator.com"
  ]
}`}
          </pre>
        </div>
      </div>
    </div>
  );
}
