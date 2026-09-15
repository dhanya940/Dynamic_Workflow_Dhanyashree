const API="";
const app=document.getElementById("app"),nav=document.getElementById("nav");
const token=()=>localStorage.getItem("token");
const esc=s=>String(s??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
function toast(msg){const d=document.createElement("div");d.className="toast";d.textContent=msg;document.getElementById("toast").append(d);setTimeout(()=>d.remove(),2500)}
async function api(path,opts={}){opts.headers={"Content-Type":"application/json",...(opts.headers||{})};if(token())opts.headers.Authorization="Bearer "+token();let r=await fetch(API+path,opts);let t=await r.text();let data=t?JSON.parse(t):null;if(!r.ok)throw new Error(data?.detail||"Request failed");return data}

function toggleTheme(){const isDark=document.documentElement.getAttribute("data-theme")==="dark";document.documentElement.setAttribute("data-theme",isDark?"light":"dark");localStorage.setItem("theme",isDark?"light":"dark")}
function loadTheme(){const saved=localStorage.getItem("theme");if(saved){document.documentElement.setAttribute("data-theme",saved)}else if(window.matchMedia("(prefers-color-scheme: dark)").matches){document.documentElement.setAttribute("data-theme","dark")}}
loadTheme();

function navBar(){const themeIcon=document.documentElement.getAttribute("data-theme")==="dark"?"☀️":"🌙";nav.innerHTML=token()?`<button class="theme-toggle" onclick="toggleTheme()">${themeIcon}</button><a href="#home">Home</a><a href="#forms">Forms</a><button onclick="logout()">Sign out</button>`:`<button class="theme-toggle" onclick="toggleTheme()">${themeIcon}</button><a href="#signin">Sign in</a><a href="#signup">Sign up</a>`}
function logout(){localStorage.removeItem("token");location.hash="#signin"}
function shell(title,body){navBar();app.innerHTML=`<div class="container"><div class="between"><div><h1>${title}</h1></div></div>${body}</div>`}
function err(e){toast(e.message)}
function requireAuth(){if(!token()){location.hash="#signin";return false}return true}

function signup(){navBar();app.innerHTML=`<div class="auth card"><h1>Create account</h1><p class="muted">Signup</p><label>Full name</label><input id="name" class="input"><label>Email</label><input id="email" type="email" class="input"><label>Password</label><input id="pass" type="password" class="input"><button class="btn primary" onclick="doSignup()">Sign up</button><p>Already registered? <a href="#signin">Sign in</a></p><div id="error" class="error"></div></div>`}
async function doSignup(){try{await api("/auth/signup",{method:"POST",body:JSON.stringify({full_name:document.getElementById("name").value,email:document.getElementById("email").value,password:document.getElementById("pass").value})});toast("Account created");location.hash="#signin"}catch(e){document.getElementById("error").textContent=e.message}}
function signin(){navBar();app.innerHTML=`<div class="auth card"><h1>Sign in</h1><p class="muted">Signin</p><label>Email</label><input id="email" type="email" class="input"><label>Password</label><input id="pass" type="password" class="input"><button class="btn primary" onclick="doSignin()">Sign in</button><p>New user? <a href="#signup">Create account</a></p><div id="error" class="error"></div></div>`}
async function doSignin(){try{let d=await api("/auth/signin",{method:"POST",body:JSON.stringify({email:document.getElementById("email").value,password:document.getElementById("pass").value})});localStorage.setItem("token",d.access_token);location.hash="#home"}catch(e){document.getElementById("error").textContent=e.message}}
async function home(){if(!requireAuth())return;try{let u=await api("/auth/home");shell("Home",`<div class="card"><h2>Welcome, ${esc(u.full_name)} 👋</h2><p class="muted">You are signed in. Create and manage dynamic forms from the Forms page.</p><a class="btn primary" href="#forms">Open Form Management</a></div>`)}catch(e){logout()}}

async function forms(){if(!requireAuth())return;try{let fs=await api("/forms");shell("My Forms",`<div class="card"><div class="between"><input id="search" class="input" style="max-width:420px" placeholder="Search forms..." oninput="filterForms()"><a class="btn primary" href="#create">+ Create form</a></div></div><div id="formList" class="grid"></div>`);window.allForms=fs;renderForms(fs)}catch(e){err(e)}}
function renderForms(fs){document.getElementById("formList").innerHTML=fs.length?fs.map(f=>`<div class="card formcard"><div class="between"><h2>${esc(f.title)}</h2><span class="badge ${f.status}">${f.status}</span></div><p class="muted">Updated ${new Date(f.updated_at).toLocaleString()}</p><div class="actions"><a class="btn" href="#builder/${f.id}">Open</a><a class="btn" href="#submissions/${f.id}">View Submissions</a></div></div>`).join(""):`<div class="card empty">No forms yet. Create your first form.</div>`}
function filterForms(){let q=search.value.toLowerCase();renderForms(allForms.filter(f=>f.title.toLowerCase().includes(q)))}
function createForm(){if(!requireAuth())return;shell("Create Form",`<div class="card"><label>Form title</label><input id="title" class="input" placeholder="Job Application"><label>Description</label><textarea id="desc" class="input" rows="4"></textarea><div class="actions"><button class="btn primary" onclick="doCreate()">Create</button><a class="btn" href="#forms">Cancel</a></div></div>`)}
async function doCreate(){try{let f=await api("/forms",{method:"POST",body:JSON.stringify({title:document.getElementById("title").value,description:document.getElementById("desc").value||null})});toast("Form created");location.hash="#builder/"+f.id}catch(e){err(e)}}

let currentForm=null;
async function builder(id){if(!requireAuth())return;try{let f=await api("/forms/"+id);currentForm=f;shell("Form Builder",builderHTML(f));renderFields();await loadRules()}catch(e){err(e)}}
function builderHTML(f){return `<div class="card"><div class="between"><div><h2>${esc(f.title)}</h2><p class="muted">${esc(f.description||"")}</p><span class="badge ${f.status}">${f.status}</span> <span class="badge">Editing v${f.editing_version_number||1}</span></div><div class="actions"><button class="btn" onclick="editForm('${f.id}')">Edit form</button>${f.status!=="archived"?`<button class="btn" onclick="publishForm('${f.id}')">Publish</button>`:""}${f.status!=="archived"?`<button class="btn danger" onclick="archiveForm('${f.id}')">Archive</button>`:""}<a class="btn" href="#versions/${f.id}">Versions</a>${f.status==="published"?`<button class="btn primary" onclick="shareForm('${f.id}')">Share</button>`:""}</div></div></div>
<div class="card"><div class="between"><h2>Fields</h2><button class="btn primary" onclick="newField()">+ Add field</button></div><p class="muted">Drag-and-drop is represented by the Up/Down controls so the same display_order API is exercised.</p><div id="fields"></div></div>
<div class="card"><h2>Conditional rules</h2><p class="muted">Example: Experience = Yes → show Years of Experience.</p><div id="rules"></div><button class="btn" onclick="newRule()">+ Add rule</button></div>`}
async function refreshBuilder(){let f=await api("/forms/"+currentForm.id);currentForm=f;app.querySelector(".container").innerHTML=`<div class="between"><h1>Form Builder</h1></div>`+builderHTML(f);renderFields();renderRules()}
function renderFields(){let el=document.getElementById("fields"),fs=currentForm.fields||[];el.innerHTML=fs.length?fs.map((f,i)=>`<div class="field" draggable="true" data-index="${i}" ondragstart="dragStart(event)" ondragover="dragOver(event)" ondrop="dropField(event)" ondragend="dragEnd(event)"><div class="field-head"><div><strong>${esc(f.label)}</strong> <span class="badge">${esc(f.field_type)}</span> ${f.is_required?'<span class="badge">required</span>':''}<br><small class="muted">${esc(f.placeholder||"")}</small></div><div><button class="btn small" onclick="moveField(${i},-1)">↑</button><button class="btn small" onclick="moveField(${i},1)">↓</button><button class="btn small" onclick="editField('${f.id}')">Edit</button><button class="btn small danger" onclick="deleteField('${f.id}')">Delete</button></div></div>${(f.options||[]).length?`<p class="muted">Options: ${f.options.map(o=>esc(o.option_label)).join(", ")}</p>`:""}</div>`).join(""):`<div class="empty">No fields. Add Name, Email, Experience, Resume, etc.</div>`}
function renderRules(){let el=document.getElementById("rules"),rs=window.rules||[];el.innerHTML=rs.length?rs.map(r=>{let a=currentForm.fields.find(f=>f.id===r.trigger_field_id)?.label||"field",b=currentForm.fields.find(f=>f.id===r.target_field_id)?.label||"field";return `<div class="rule"><strong>${esc(a)}</strong> ${esc(r.operator)} "${esc(r.comparison_value)}" → ${esc(r.action)} <strong>${esc(b)}</strong> <button class="btn small" onclick="editRule('${r.id}')">Edit</button><button class="btn small danger" onclick="deleteRule('${r.id}')">Delete</button></div>`}).join(""):`<p class="muted">No rules yet.</p>`}
async function loadRules(){window.rules=await api("/forms/"+currentForm.id+"/rules");renderRules()}
async function newField(){let html=`<div class="card"><h2>Add field</h2>${fieldEditor()}</div>`;app.querySelector(".container").insertAdjacentHTML("afterbegin",html)}
function fieldEditor(f={}){let opts=(f.options||[]).map(o=>`${o.option_label}|${o.option_value}`).join("\n");return `<label>Field Label *</label><input id="flabel" class="input" value="${esc(f.label||"")}" placeholder="e.g., Full Name"><label>Field Type *</label><select id="ftype" class="input" onchange="toggleOptionsVisibility()"><option value="text" ${f.field_type==="text"?"selected":""}>Text</option><option value="email" ${f.field_type==="email"?"selected":""}>Email</option><option value="number" ${f.field_type==="number"?"selected":""}>Number</option><option value="date" ${f.field_type==="date"?"selected":""}>Date</option><option value="dropdown" ${f.field_type==="dropdown"?"selected":""}>Dropdown</option><option value="checkbox" ${f.field_type==="checkbox"?"selected":""}>Checkbox</option><option value="file" ${f.field_type==="file"?"selected":""}>File Upload</option><option value="textarea" ${f.field_type==="textarea"?"selected":""}>Textarea</option></select><label>Placeholder</label><input id="fph" class="input" value="${esc(f.placeholder||"")}" placeholder="e.g., Enter your name"><label><input id="freq" type="checkbox" ${f.is_required?"checked":""}> Required field</label><label>Validation Config (JSON, optional)</label><input id="fval" class="input" placeholder='{"min":0,"max":100}' value='${esc(f.validation_config?JSON.stringify(f.validation_config):"")}'> <div id="optionsSection" style="display:${["dropdown","checkbox"].includes(f.field_type)?"block":"none"}"><label>Options (one <code>label|value</code> per line) *</label><textarea id="fopts" class="input" rows="4" placeholder="Option 1|value1&#10;Option 2|value2">${esc(opts)}</textarea></div><div class="actions"><button class="btn primary" onclick="${f.id?`saveField('${f.id}')`:"saveNewField()"}">Save Field</button><button class="btn" onclick="this.closest('.card').remove()">Cancel</button></div>`}

function toggleOptionsVisibility(){let type=ftype.value;let optsDiv=document.getElementById("optionsSection");if(optsDiv){optsDiv.style.display=["dropdown","checkbox"].includes(type)?"block":"none"}}
function fieldPayload(){let validation=null;if(fval.value.trim())try{validation=JSON.parse(fval.value)}catch(e){throw Error("Validation JSON is invalid")}let options=fopts.value.split("\n").map(x=>x.trim()).filter(Boolean).map((x,i)=>{let [a,...b]=x.split("|");return {option_label:a,option_value:b.join("|")||a,display_order:i}});return {label:flabel.value,field_type:ftype.value,placeholder:fph.value||null,is_required:freq.checked,validation_config:validation,options:options.length?options:null}}
async function saveNewField(){try{await api("/forms/"+currentForm.id+"/fields",{method:"POST",body:JSON.stringify(fieldPayload())});toast("Field added");await builder(currentForm.id)}catch(e){err(e)}}
function editField(id){let f=currentForm.fields.find(x=>x.id===id);let d=document.createElement("div");d.className="card";d.innerHTML=`<h2>Edit field</h2>${fieldEditor(f)}`;app.querySelector(".container").prepend(d)}
async function saveField(id){try{await api("/fields/"+id,{method:"PUT",body:JSON.stringify(fieldPayload())});toast("Field updated");await builder(currentForm.id)}catch(e){err(e)}}
async function deleteField(id){if(!confirm("Delete this field?"))return;try{await api("/fields/"+id,{method:"DELETE"});await builder(currentForm.id)}catch(e){err(e)}}
async function moveField(i,delta){let fs=[...currentForm.fields],j=i+delta;if(j<0||j>=fs.length)return;[fs[i],fs[j]]=[fs[j],fs[i]];try{await api("/forms/"+currentForm.id+"/reorder-fields",{method:"PATCH",body:JSON.stringify({order:fs.map((f,k)=>({field_id:f.id,display_order:k}))})});await builder(currentForm.id)}catch(e){err(e)}}
let dragIndex=null;
function dragStart(e){dragIndex=Number(e.currentTarget.dataset.index);e.currentTarget.classList.add("dragging");e.dataTransfer.effectAllowed="move"}
function dragOver(e){e.preventDefault();e.currentTarget.classList.add("dropzone")}
function dragEnd(e){e.currentTarget.classList.remove("dragging","dropzone");document.querySelectorAll(".field").forEach(x=>x.classList.remove("dropzone"))}
async function dropField(e){e.preventDefault();let to=Number(e.currentTarget.dataset.index);if(dragIndex===null||dragIndex===to)return;let fs=[...currentForm.fields],m=fs.splice(dragIndex,1)[0];fs.splice(to,0,m);try{await api("/forms/"+currentForm.id+"/reorder-fields",{method:"PATCH",body:JSON.stringify({order:fs.map((f,k)=>({field_id:f.id,display_order:k}))})});await builder(currentForm.id)}catch(x){err(x)}finally{dragIndex=null}}
function editForm(id){let f=currentForm;app.querySelector(".container").insertAdjacentHTML("afterbegin",`<div class="card"><h2>Edit form</h2><label>Title</label><input id="etitle" class="input" value="${esc(f.title)}"><label>Description</label><textarea id="edesc" class="input">${esc(f.description||"")}</textarea><button class="btn primary" onclick="saveForm('${id}')">Save</button></div>`)}
async function saveForm(id){try{await api("/forms/"+id,{method:"PUT",body:JSON.stringify({title:etitle.value,description:edesc.value||null})});await builder(id)}catch(e){err(e)}}
async function archiveForm(id){if(!confirm("Archive this form? It will stop public access."))return;try{await api("/forms/"+id+"/archive",{method:"PATCH"});await builder(id)}catch(e){err(e)}}
async function publishForm(id){if(!confirm("Publish the current draft?"))return;try{await api("/forms/"+id+"/publish",{method:"POST"});toast("Published");await builder(id)}catch(e){err(e)}}
async function shareForm(id){try{let d=await api("/forms/"+id+"/generate-link",{method:"POST"});let url=location.origin+"/form/"+d.slug;app.insertAdjacentHTML("beforeend",`<div class="modal" id="shareModal"><div class="modalbox"><h2>Share Form</h2><p class="muted">Published version ${d.form_version_number}</p><input id="shareUrl" class="input" value="${esc(url)}" readonly><div class="actions"><button class="btn primary" onclick="copyShare()">Copy Link</button><a class="btn" href="${esc(url)}" target="_blank">Open Form</a><button class="btn" onclick="document.getElementById('shareModal').remove()">Close</button></div></div></div>`)}catch(e){err(e)}}
async function copyShare(){let x=document.getElementById("shareUrl");await navigator.clipboard.writeText(x.value);toast("Link copied")}
function newRule(){let fs=currentForm.fields||[];if(fs.length<2)return toast("Add at least two fields first");app.querySelector(".container").insertAdjacentHTML("afterbegin",`<div class="card" id="ruleEditor"><h2>Add conditional rule</h2><label>When field</label><select id="rtrigger" class="input">${fs.map(f=>`<option value="${f.id}">${esc(f.label)}</option>`).join("")}</select><label>Operator</label><select id="rop" class="input"><option value="equals">equals</option><option value="not_equals">not equals</option><option value="contains">contains</option><option value="greater_than">greater than</option><option value="is_empty">is empty</option></select><label>Value</label><input id="rvalue" class="input"><label>Action</label><select id="raction" class="input"><option value="show">show</option><option value="hide">hide</option><option value="require">require</option></select><label>Target field</label><select id="rtarget" class="input">${fs.map(f=>`<option value="${f.id}">${esc(f.label)}</option>`).join("")}</select><button class="btn primary" onclick="saveRule()">Save rule</button><button class="btn" onclick="document.getElementById('ruleEditor').remove()">Cancel</button></div>`)}

async function editRule(ruleId){let rule=window.rules.find(r=>r.id===ruleId);if(!rule)return;let fs=currentForm.fields||[];app.querySelector(".container").insertAdjacentHTML("afterbegin",`<div class="card" id="ruleEditor"><h2>Edit conditional rule</h2><label>When field</label><select id="rtrigger" class="input">${fs.map(f=>`<option value="${f.id}" ${f.id===rule.trigger_field_id?"selected":""}>${esc(f.label)}</option>`).join("")}</select><label>Operator</label><select id="rop" class="input"><option value="equals" ${rule.operator==="equals"?"selected":""}>equals</option><option value="not_equals" ${rule.operator==="not_equals"?"selected":""}>not equals</option><option value="contains" ${rule.operator==="contains"?"selected":""}>contains</option><option value="greater_than" ${rule.operator==="greater_than"?"selected":""}>greater than</option><option value="is_empty" ${rule.operator==="is_empty"?"selected":""}>is empty</option></select><label>Value</label><input id="rvalue" class="input" value="${esc(rule.comparison_value)}"><label>Action</label><select id="raction" class="input"><option value="show" ${rule.action==="show"?"selected":""}>show</option><option value="hide" ${rule.action==="hide"?"selected":""}>hide</option><option value="require" ${rule.action==="require"?"selected":""}>require</option></select><label>Target field</label><select id="rtarget" class="input">${fs.map(f=>`<option value="${f.id}" ${f.id===rule.target_field_id?"selected":""}>${esc(f.label)}</option>`).join("")}</select><button class="btn primary" onclick="updateRule('${ruleId}')">Update rule</button><button class="btn" onclick="document.getElementById('ruleEditor').remove()">Cancel</button></div>`)}
async function saveRule(){try{await api("/forms/"+currentForm.id+"/rules",{method:"POST",body:JSON.stringify({trigger_field_id:rtrigger.value,operator:rop.value,comparison_value:rvalue.value,target_field_id:rtarget.value,action:raction.value})});toast("Rule added");document.getElementById("ruleEditor").remove();await builder(currentForm.id);await loadRules()}catch(e){err(e)}}

async function updateRule(ruleId){try{await api("/forms/rules/"+ruleId,{method:"PUT",body:JSON.stringify({operator:rop.value,comparison_value:rvalue.value,target_field_id:rtarget.value,action:raction.value})});toast("Rule updated");document.getElementById("ruleEditor").remove();await builder(currentForm.id);await loadRules()}catch(e){err(e)}}
async function deleteRule(id){try{await api("/forms/rules/"+id,{method:"DELETE"});await builder(currentForm.id);await loadRules()}catch(e){err(e)}}

async function versions(id){if(!requireAuth())return;try{let vs=await api("/forms/"+id+"/versions");shell("Version History",`<div class="card"><a class="btn" href="#builder/${id}">← Builder</a></div>${vs.map(v=>`<div class="card"><div class="between"><h2>Version ${v.version_number}</h2><span class="badge ${v.is_active?"published":""}">${v.is_active?"ACTIVE":"Draft/old"}</span></div><p class="muted">${v.published_at?"Published "+new Date(v.published_at).toLocaleString():"Not published"}</p><a class="btn" href="#version/${id}/${v.version_number}">View details</a></div>`).join("")}`)}catch(e){err(e)}}
async function versionDetail(id,n){if(!requireAuth())return;try{let v=await api(`/forms/${id}/versions/${n}`);shell(`Version ${n}`,`<div class="card"><a class="btn" href="#versions/${id}">← Version history</a><span class="badge ${v.is_active?"published":""}">${v.is_active?"ACTIVE":"READ ONLY"}</span></div><div class="card"><h2>Fields</h2>${v.fields.map(f=>`<div class="field"><strong>${esc(f.label)}</strong> — ${esc(f.field_type)} ${f.is_required?"(required)":""}</div>`).join("")}</div><div class="card"><h2>Rules</h2>${v.rules?.length?v.rules.map(r=>`<div class="rule">${esc(r.operator)} "${esc(r.comparison_value)}" → ${esc(r.action)}</div>`).join(""):"No rules"}</div>`)}catch(e){err(e)}}

async function submissions(id){if(!requireAuth())return;try{let f=await api("/forms/"+id);let subs=await api("/forms/"+id+"/submissions");shell(`Submissions - ${esc(f.title)}`,`<div class="card"><a class="btn" href="#forms">← Forms</a></div>${subs.length?`<div class="card"><h2>${subs.length} Submission(s)</h2>${subs.map(s=>`<div class="submission-item"><div class="between"><strong>Response ID: ${esc(s.response_id)}</strong><span class="muted">${new Date(s.submitted_at).toLocaleString()}</span></div><p class="muted">Time: ${s.completion_time_seconds}s</p><a class="btn" href="#submission/${id}/${s.id}">View Details</a></div>`).join("")}</div>`:`<div class="card empty">No submissions yet.</div>`}`)}catch(e){err(e)}}

async function submissionDetail(formId,subId){if(!requireAuth())return;try{let s=await api("/forms/"+formId+"/submissions/"+subId);window.currentSubmission=s;shell("Submission Details",`<div class="card"><a class="btn" href="#submissions/${formId}">← Back to submissions</a></div><div class="card"><div class="between"><h2>Response ID: ${esc(s.response_id)}</h2><span class="muted">${new Date(s.submitted_at).toLocaleString()}</span></div><p class="muted">Completion time: ${s.completion_time_seconds}s</p></div><div class="card"><h2>Responses</h2><div id="responses"></div></div>`);renderResponses()}catch(e){err(e)}}

async function renderResponses(){let el=document.getElementById("responses");if(!el)return;let values=window.currentSubmission.values;el.innerHTML=values.map(v=>`<div class="field"><strong>${esc(v.field_label)}</strong>${isFileId(v.value)?`<div id="file-${v.field_id}"><span class="muted">Loading file info...</span></div>`:`<p>${esc(v.value)}</p>`}</div>`).join("");for(let v of values){if(isFileId(v.value)){try{let fileLink=await api("/files/"+v.value);document.getElementById(`file-${v.field_id}`).innerHTML=`<a class="file-link" href="${fileLink.download_url}" target="_blank">📎 Download file</a>`}catch(e){document.getElementById(`file-${v.field_id}`).innerHTML=`<span class="error">File not available</span>`}}}}

function isFileId(val){return /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(val)}

async function publicPage(slug){navBar();try{let f=await api("/public/forms/"+slug);let start=Date.now();app.innerHTML=`<div class="container public"><div class="card"><h1>${esc(f.title)}</h1><p class="muted">${esc(f.description||"")}</p><form id="publicForm">${f.fields.map(fieldHTML).join("")}<button class="btn primary" type="submit">Submit</button></form></div></div>`;window.publicData=f;window.uploadedFiles={};document.getElementById("publicForm").onsubmit=async e=>{e.preventDefault();let values={};for(let x of f.fields){let els=document.querySelectorAll(`[data-field="${x.id}"]`);if(x.field_type==="checkbox"){values[x.id]=[...els].filter(y=>y.checked).map(y=>y.value)}else if(x.field_type==="file"){let file=els[0].files[0];if(file){try{let fd=new FormData();fd.append("file",file);let uploaded=await api("/files/upload",{method:"POST",body:fd,headers:{}});values[x.id]=uploaded.id}catch(err){toast("File upload failed");return}}else{values[x.id]=""}}else{values[x.id]=els[0]?.value??""}}try{let d=await api("/public/forms/"+slug+"/submit",{method:"POST",body:JSON.stringify({values,completion_time_seconds:Math.floor((Date.now()-start)/1000)})});app.querySelector(".card").innerHTML=`<div class="success"><h2>Thank you!</h2><p>${esc(d.message)}</p><p>Response ID: ${esc(d.response_id)}</p></div>`}catch(e){console.log("Full error:",JSON.stringify(e,null,2));if(e.detail){let detail=e.detail;console.log("Detail:",JSON.stringify(detail,null,2));let errs=detail.errors;if(errs&&typeof errs==="object"){Object.entries(errs).forEach(([fieldId,msg])=>{let wrap=document.querySelector(`[data-wrap="${fieldId}"]`);if(wrap){let existing=wrap.querySelector(".field-error");if(existing)existing.remove();wrap.insertAdjacentHTML("beforeend",`<div class="field-error">${esc(msg)}</div>`)}})}else{toast(detail.message||"Validation failed")}}else{toast(e.message||"Submission failed")}}};applyRules()}catch(e){app.innerHTML=`<div class="container"><div class="card"><h1>Form unavailable</h1><p class="error">${esc(e.message)}</p></div></div>`}}
function fieldHTML(f){let input="";let req=f.is_required?"required":"";if(f.field_type==="textarea")input=`<textarea class="input" data-field="${f.id}" placeholder="${esc(f.placeholder||"")}" ${req}></textarea>`;else if(["dropdown"].includes(f.field_type))input=`<select class="input" data-field="${f.id}" ${req}><option value="">Select...</option>${(f.options||[]).map(o=>`<option value="${esc(o.option_value)}">${esc(o.option_label)}</option>`).join("")}</select>`;else if(f.field_type==="checkbox")input=(f.options||[]).map(o=>`<label><input type="checkbox" data-field="${f.id}" value="${esc(o.option_value)}"> ${esc(o.option_label)}</label>`).join("");else if(f.field_type==="file")input=`<input class="input" type="file" data-field="${f.id}" ${req}>`;else input=`<input class="input" type="${["text","email","number","date"].includes(f.field_type)?f.field_type:"text"}" data-field="${f.id}" placeholder="${esc(f.placeholder||"")}" ${req}>`;return `<div class="field" data-wrap="${f.id}"><label>${esc(f.label)} ${f.is_required?"*":""}</label>${input}</div>`}
function applyRules(){let rs=publicData.rules||[];rs.forEach(r=>{let trigger=document.querySelector(`[data-field="${r.trigger_field_id}"]`);let target=document.querySelector(`[data-wrap="${r.target_field_id}"]`);if(!trigger||!target)return;let fn=()=>{let val=trigger.type==="checkbox"?trigger.checked?trigger.value:"":trigger.value;let yes=r.operator==="equals"?val===r.comparison_value:r.operator==="not_equals"?val!==r.comparison_value:String(val).includes(r.comparison_value);target.classList.toggle("hidden",(r.action==="show")?yes:!yes)};trigger.addEventListener("input",fn);trigger.addEventListener("change",fn);fn()})}

async function route(){if(location.pathname.startsWith("/form/"))return publicPage(location.pathname.split("/")[2]);let p=location.hash.slice(1)||"home";if(p.startsWith("form/"))return publicPage(p.split("/")[1]);let [r,a,b]=p.split("/");if(r==="signup")return signup();if(r==="signin")return signin();if(r==="home")return home();if(r==="forms")return forms();if(r==="create")return createForm();if(r==="builder")return builder(a);if(r==="versions")return versions(a);if(r==="version")return versionDetail(a,b);if(r==="submissions")return submissions(a);if(r==="submission")return submissionDetail(a,b);return token()?home():signin()}
window.addEventListener("hashchange",route);route();
function applyConditionalRules(form, rules) {

    function getValue(fieldId) {

        const elements =
            document.querySelectorAll(
                `[data-field="${fieldId}"]`
            );

        if (!elements.length) {
            return "";
        }

        if (elements[0].type === "checkbox") {

            return [...elements]
                .filter(x => x.checked)
                .map(x => x.value);
        }

        return elements[0].value;
    }


    function compare(value, operator, expected) {

        if (operator === "equals") {

            if (Array.isArray(value)) {
                return value.includes(expected);
            }

            return String(value) === String(expected);
        }


        if (operator === "not_equals") {

            return String(value) !== String(expected);
        }


        if (operator === "contains") {

            return String(value)
                .toLowerCase()
                .includes(
                    String(expected).toLowerCase()
                );
        }


        if (operator === "greater_than") {

            return Number(value) > Number(expected);
        }


        if (operator === "is_empty") {

            return (
                value === "" ||
                value === null ||
                value === undefined
            );
        }

        return false;
    }


    function refresh() {

        rules.forEach(rule => {

            const target =
                document.querySelector(
                    `[data-wrap="${rule.target_field_id}"]`
                );

            if (!target) {
                return;
            }

            const value =
                getValue(rule.trigger_field_id);

            const condition =
                compare(
                    value,
                    rule.operator,
                    rule.comparison_value
                );


            if (rule.action === "show") {

                target.style.display =
                    condition ? "" : "none";
            }


            if (rule.action === "hide") {

                target.style.display =
                    condition ? "none" : "";
            }


            if (rule.action === "require") {

                const input =
                    target.querySelector(
                        "[data-field]"
                    );

                if (input) {
                    input.required = condition;
                }
            }

        });
    }


    document
        .querySelectorAll("[data-field]")
        .forEach(input => {

            input.addEventListener(
                "change",
                refresh
            );

            input.addEventListener(
                "input",
                refresh
            );
        });


    refresh();
}