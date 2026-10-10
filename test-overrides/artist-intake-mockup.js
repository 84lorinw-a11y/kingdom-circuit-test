"use strict";
(() => {
  const form = document.querySelector("#artist-intake-demo-form");
  if (!form) return;
  const photo = form.querySelector("#ai-photo");
  const image = form.querySelector("#ai-photo-preview");
  const icon = form.querySelector(".ai-photo-icon");
  const status = form.querySelector("#ai-photo-status");
  const remove = form.querySelector("#ai-remove-photo");
  const pickLabel = form.querySelector("#ai-pick-label");
  const review = form.querySelector("#ai-review");
  let selectedPhoto = null;
  let revision = 0;
  function setPhoto(file) {
    const current = ++revision;
    selectedPhoto = null;
    image.hidden = true;
    image.removeAttribute("src");
    icon.hidden = false;
    remove.hidden = true;
    pickLabel.textContent = "Choose photo";
    status.classList.remove("is-error");
    review.hidden = true;
    if (!file) { status.textContent = "No photo selected."; return; }
    if (!/\.(jpe?g|png|webp|hei[cf])$/i.test(file.name) || file.size > 10 * 1024 * 1024 || file.size === 0) {
      status.textContent = "Choose a JPG, PNG, WebP or HEIC photo under 10 MB.";
      status.classList.add("is-error"); photo.value = ""; return;
    }
    selectedPhoto = file;
    pickLabel.textContent = "Change photo";
    remove.hidden = false;
    const size = file.size < 1024 * 1024 ? `${Math.ceil(file.size / 1024)} KB` : `${(file.size / 1024 / 1024).toFixed(1)} MB`;
    status.textContent = `${file.name} · ${size}`;
    const reader = new FileReader();
    reader.onload = () => {
      if (current !== revision) return;
      image.onload = () => { if (current !== revision) return; image.hidden = false; icon.hidden = true; };
      image.onerror = () => {
        if (current !== revision) return;
        image.hidden = true; icon.hidden = false;
        if (/\.hei[cf]$/i.test(file.name)) status.textContent = `${file.name} · ${size} · Selected. This browser can’t preview HEIC.`;
        else { selectedPhoto = null; photo.value = ""; status.classList.add("is-error"); status.textContent = "We couldn’t open that photo. Try another JPG, PNG or WebP."; }
      };
      image.src = String(reader.result);
    };
    reader.onerror = () => { if (current !== revision) return; selectedPhoto = null; photo.value = ""; status.classList.add("is-error"); status.textContent = "We couldn’t read that photo. Please try another."; };
    reader.readAsDataURL(file);
  }
  photo.addEventListener("change", () => setPhoto(photo.files[0]));
  remove.addEventListener("click", () => { photo.value = ""; setPhoto(null); photo.focus(); });
  const dropzone = form.querySelector("#ai-dropzone");
  for (const name of ["dragover", "drop"]) dropzone.addEventListener(name, e => e.preventDefault());
  dropzone.addEventListener("dragover", () => dropzone.classList.add("is-dragging"));
  dropzone.addEventListener("dragleave", () => dropzone.classList.remove("is-dragging"));
  dropzone.addEventListener("drop", e => { dropzone.classList.remove("is-dragging"); photo.value = ""; setPhoto(e.dataTransfer.files[0]); });
  // This mockup intentionally has no transport, storage, form action or submission endpoint.
  form.addEventListener("submit", e => e.preventDefault());
  form.addEventListener("input", () => { review.hidden = true; });
  const fields = ["website", "instagram", "spotify", "youtube"];
  form.querySelector("#ai-submit-preview").addEventListener("click", () => {
    const links = {};
    for (const field of fields) {
      const value = form.elements.namedItem(field).value;
      if (value.trim()) links[field] = value;
    }
    const details = form.querySelector("#ai-review-details");
    details.replaceChildren();
    const values = [["Artist",form.elements.namedItem("artistName").value || "Not provided"],["Email",form.elements.namedItem("email").value || "Not provided"],["Photo",selectedPhoto ? selectedPhoto.name : "No photo selected"],...Object.entries(links)];
    for (const [label,value] of values) { const dt = document.createElement("dt"); const dd = document.createElement("dd"); dt.textContent = label[0].toUpperCase()+label.slice(1); dd.textContent = value; details.append(dt,dd); }
    review.hidden = false; review.focus(); review.scrollIntoView({behavior:"smooth",block:"nearest"});
  });
  form.querySelector("#ai-edit").addEventListener("click", () => { review.hidden = true; form.querySelector("#ai-name").focus(); });
})();
