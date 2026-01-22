// Mobile nav toggle
const navToggle = document.getElementById('nav-toggle');
const primaryNav = document.getElementById('primary-nav');
if(navToggle){
  navToggle.addEventListener('click', ()=>{
    const expanded = navToggle.getAttribute('aria-expanded') === 'true';
    navToggle.setAttribute('aria-expanded', String(!expanded));
    primaryNav.setAttribute('aria-hidden', String(expanded));
  });
}

// Smooth scroll for internal links
document.querySelectorAll('a[href^="#"]').forEach(a=>{
  a.addEventListener('click', (e)=>{
    const href = a.getAttribute('href');
    if(href.length>1){
      e.preventDefault();
      const el = document.querySelector(href);
      if(el) el.scrollIntoView({behavior:'smooth', block:'start'});
      // close mobile nav after clicking
      if(window.innerWidth <= 640 && primaryNav){
        navToggle.setAttribute('aria-expanded','false');
        primaryNav.setAttribute('aria-hidden','true');
      }
    }
  });
});

// Contact form handler (client-side only)
const form = document.getElementById('contact-form');
const formMsg = document.getElementById('form-msg');
if(form){
  form.addEventListener('submit', (e)=>{
    e.preventDefault();
    const formData = new FormData(form);
    const name = formData.get('name');
    // Simple form feedback — no back-end
    form.reset();
    formMsg.textContent = `Thanks ${name || 'there'} — your message was received (demo).`;
    setTimeout(()=>{ formMsg.textContent = ''; }, 6000);
  });
}

// Footer year
const yearEl = document.getElementById('year');
if(yearEl) yearEl.textContent = new Date().getFullYear();
