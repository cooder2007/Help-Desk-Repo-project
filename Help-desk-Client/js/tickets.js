import { api } from './api.js';
import { getAuth } from './auth.js';

const ticketsListEl = document.getElementById('ticketsList');
const ticketForm = document.getElementById('ticketForm');
const ticketResult = document.getElementById('ticketResult');

async function loadTickets() {
  const { token } = getAuth();
  if (!token) {
    ticketsListEl.innerHTML = '<p class="notice">Please log in to view your tickets.</p>';
    return;
  }
  try {
    const tickets = await api('/tickets', { token });
    ticketsListEl.innerHTML = tickets
      .map(
        (t) => `
        <div class="ticket">
          <div><strong>${t.title}</strong></div>
          <div class="meta">#${t.id} • ${t.category} • ${t.status} • Priority: ${t.priority}</div>
          <button data-id="${t.id}" class="viewTicketBtn">View</button>
        </div>`
      )
      .join('');
    bindViewButtons();
  } catch (e) {
    ticketsListEl.innerHTML = `<p class="notice">Error loading tickets: ${e.message}</p>`;
  }
}

function bindViewButtons() {
  document.querySelectorAll('.viewTicketBtn').forEach((btn) => {
    btn.addEventListener('click', async () => {
      const id = btn.getAttribute('data-id');
      await openTicketModal(id);
    });
  });
}

async function openTicketModal(id) {
  const { token } = getAuth();
  try {
    const data = await api(`/tickets/${id}`, { token });
    const modal = document.createElement('div');
    modal.className = 'card';
    modal.style.position = 'fixed';
    modal.style.top = '10%';
    modal.style.left = '50%';
    modal.style.transform = 'translateX(-50%)';
    modal.style.maxWidth = '700px';
    modal.style.zIndex = '1000';

    modal.innerHTML = `
      <h3>Ticket #${data.ticket.id}: ${data.ticket.title}</h3>
      <p class="meta">${data.ticket.category} • ${data.ticket.status}</p>
      <div style="max-height: 300px; overflow:auto; border:1px solid #1f2937; padding:8px; border-radius:8px;">
        ${data.messages
          .map(
            (m) => `
          <div style="margin-bottom:8px;">
            <strong>${m.author_name} (${m.author_role})</strong>
            <div>${m.message}</div>
            <div class="meta">${new Date(m.created_at).toLocaleString()}</div>
          </div>`
          )
          .join('')}
      </div>
      <form id="replyForm" style="margin-top:10px;">
        <textarea name="message" required minlength="2" placeholder="Write a reply..."></textarea>
        <button type="submit">Send</button>
        <button type="button" id="closeModal">Close</button>
      </form>
    `;

    document.body.appendChild(modal);

    modal.querySelector('#closeModal').addEventListener('click', () => modal.remove());

    modal.querySelector('#replyForm').addEventListener('submit', async (e) => {
      e.preventDefault();
      const message = e.target.message.value.trim();
      if (!message) return;
      try {
        await api(`/tickets/${id}/messages`, { method: 'POST', body: { message }, token });
        modal.remove();
        await loadTickets();
      } catch (err) {
        alert('Failed to send message: ' + err.message);
      }
    });
  } catch (e) {
    alert('Failed to load ticket: ' + e.message);
  }
}

if (ticketForm) {
  ticketForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const form = new FormData(ticketForm);
    const payload = {
      title: form.get('title'),
      category: form.get('category'),
      priority: form.get('priority'),
      description: form.get('description'),
    };
    const { token } = getAuth();
    if (!token) {
      ticketResult.textContent = 'Please log in first.';
      return;
    }
    try {
      const created = await api('/tickets', { method: 'POST', body: payload, token });
      ticketResult.textContent = `Ticket #${created.id} created.`;
      ticketForm.reset();
      await loadTickets();
    } catch (err) {
      ticketResult.textContent = 'Error: ' + err.message;
    }
  });
}

export async function initTickets() {
  await loadTickets();
}