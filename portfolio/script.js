// Mobile nav toggle
const navToggle = document.querySelector('.nav-toggle');
const siteNav = document.querySelector('.site-nav');
navToggle && navToggle.addEventListener('click', ()=>{
  const expanded = navToggle.getAttribute('aria-expanded') === 'true';
  navToggle.setAttribute('aria-expanded', String(!expanded));
  siteNav.style.display = siteNav.style.display === 'block' ? '' : 'block';
});

// Contact form handling (client-side only)
const form = document.getElementById('contact-form');
const formMsg = document.getElementById('form-msg');
if(form){
  form.addEventListener('submit', (e)=>{
    e.preventDefault();
    const data = new FormData(form);
    // Simple client-side validation
    const name = data.get('name').toString().trim();
    const email = data.get('email').toString().trim();
    const message = data.get('message').toString().trim();
    if(!name || !email || !message){
      formMsg.textContent = 'Please fill out all fields.'; formMsg.style.color = 'darkred';
      return;
    }
    // Simulate success
    formMsg.style.color = 'green';
    formMsg.textContent = 'Thanks! Your message has been received (this is a demo).';
    form.reset();
  });
}

// Set year in footer
const yearSpan = document.getElementById('year');
if(yearSpan) yearSpan.textContent = new Date().getFullYear();
