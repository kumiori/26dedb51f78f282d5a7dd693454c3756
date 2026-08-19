"""Browser-only AES-256-GCM encryption and direct presigned upload component."""

from __future__ import annotations

import streamlit as st


HTML = """
<section class="drop">
  <label for="takeover-file">SELECT FILE</label>
  <input id="takeover-file" type="file" />
  <button id="takeover-enter" disabled>ENCRYPT + ENTER TAKE OVER</button>
  <p id="takeover-state">PLAINTEXT STAYS IN THIS BROWSER</p>
</section>
"""

CSS = """
.drop { border:1px solid #111; padding:18px; font-family:monospace; display:grid; gap:14px; }
label { font-size:12px; letter-spacing:.08em; }
input { border:1px dashed #555; padding:18px; }
button { padding:14px; border:1px solid #111; background:#111; color:white; cursor:pointer; }
button:disabled { opacity:.4; cursor:not-allowed; }
p { margin:0; font-size:11px; letter-spacing:.05em; }
"""

JS = r"""
function bytesToBase64Url(bytes) {
  let raw = '';
  bytes.forEach((byte) => raw += String.fromCharCode(byte));
  return btoa(raw).replaceAll('+', '-').replaceAll('/', '_').replaceAll('=', '');
}

function hexToBytes(hex) {
  return new Uint8Array(hex.match(/.{1,2}/g).map((pair) => parseInt(pair, 16)));
}

export default function(component) {
  const { data, setTriggerValue, parentElement } = component;
  const input = parentElement.querySelector('#takeover-file');
  const button = parentElement.querySelector('#takeover-enter');
  const state = parentElement.querySelector('#takeover-state');

  input.onchange = () => {
    button.disabled = !input.files.length;
    state.textContent = input.files.length ? `${input.files[0].name} · READY` : 'PLAINTEXT STAYS IN THIS BROWSER';
  };

  button.onclick = async () => {
    const file = input.files[0];
    if (!file) return;
    button.disabled = true;
    state.textContent = 'ENCRYPTING IN BROWSER…';
    try {
      const plaintext = await file.arrayBuffer();
      const fileKey = await crypto.subtle.generateKey({name:'AES-GCM', length:256}, true, ['encrypt']);
      const fileKeyBytes = new Uint8Array(await crypto.subtle.exportKey('raw', fileKey));
      const iv = crypto.getRandomValues(new Uint8Array(12));
      const ciphertext = new Uint8Array(await crypto.subtle.encrypt({name:'AES-GCM', iv}, fileKey, plaintext));

      const salt = crypto.getRandomValues(new Uint8Array(16));
      const wrapIv = crypto.getRandomValues(new Uint8Array(12));
      const identityMaterial = await crypto.subtle.importKey('raw', hexToBytes(data.identity_key), 'HKDF', false, ['deriveKey']);
      const wrappingKey = await crypto.subtle.deriveKey(
        {name:'HKDF', hash:'SHA-256', salt, info:new TextEncoder().encode(`takeover-storage-v1:${data.participant}`)},
        identityMaterial,
        {name:'AES-GCM', length:256},
        false,
        ['encrypt']
      );
      const wrappedKey = new Uint8Array(await crypto.subtle.encrypt({name:'AES-GCM', iv:wrapIv}, wrappingKey, fileKeyBytes));

      state.textContent = 'UPLOADING CIPHERTEXT…';
      const response = await fetch(data.upload_url, {
        method:'PUT',
        headers:{'Content-Type':'application/octet-stream'},
        body:new Blob([ciphertext], {type:'application/octet-stream'})
      });
      if (!response.ok) throw new Error(`Filebase returned ${response.status}`);

      plaintext.byteLength; // Keep plaintext scoped to this handler only.
      setTriggerValue('uploaded', {
        id:data.contribution_id,
        key:data.object_key,
        contributor_id:data.participant,
        filename:file.name,
        original_bytes:file.size,
        encrypted_bytes:ciphertext.byteLength,
        original_mime_type:file.type || 'application/octet-stream',
        algorithm:'AES-256-GCM',
        version:1,
        iv:bytesToBase64Url(iv),
        kdf:'HKDF-SHA-256',
        salt:bytesToBase64Url(salt),
        wrap_iv:bytesToBase64Url(wrapIv),
        wrapped_key:bytesToBase64Url(wrappedKey),
        key_reference:`participant:${data.participant}:v1`
      });
      input.value = '';
      state.textContent = 'CIPHERTEXT RECEIVED';
    } catch (error) {
      state.textContent = `FAILED · ${error.message}`;
    } finally {
      button.disabled = false;
    }
  };
}
"""


encrypted_drop = st.components.v2.component(
    "takeover_encrypted_drop_v1",
    html=HTML,
    css=CSS,
    js=JS,
)
