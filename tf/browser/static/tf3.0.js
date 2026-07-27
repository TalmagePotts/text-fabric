/*eslint-env jquery*/

/* mode: results or passage
 *
 */

// character widget


const copyChar = (el, c) => {
  for (const el of document.getElementsByClassName("ccon")) {
    el.className = "ccoff"
  }
  el.className = "ccon"
  navigator.clipboard.writeText(String.fromCharCode(c))
}
globalThis.copyChar = copyChar

const mathTypeset = dest => {
  const showMathOption = $("#math")
  const showMath = showMathOption.prop("checked")

  if (showMath) {
    const { MathJax } = globalThis
    MathJax.typeset(dest)
  }
}

const lastJobKey = "tfLastJob"

const switchMode = m => {
  const mode = $("#mode")
  const pageNav = $("#navigation")
  const pages = $("#pages")
  const nresults = $("#nresults")
  const passagesNav = $("#passagesnav")
  const passages = $("#passages")
  const sectionsTable = $("#sectionsTable")
  const tuplesTable = $("#tuplesTable")
  const queryTable = $("#queryTable")
  const passageTable = $("#passageTable")
  const resultsc = $("#moderesults")
  const passagec = $("#modepassage")

  mode.val(m)
  if (m == "passage") {
    pageNav.hide()
    pages.hide()
    nresults.hide()
    passages.show()
    passagesNav.show()
    sectionsTable.hide()
    tuplesTable.hide()
    queryTable.hide()
    passageTable.show()
    resultsc.show()
    passagec.hide()
  } else if (m == "results") {
    pageNav.show()
    pages.show()
    nresults.show()
    passagesNav.hide()
    passages.hide()
    sectionsTable.show()
    tuplesTable.show()
    queryTable.show()
    passageTable.hide()
    resultsc.hide()
    passagec.show()
  }
}

const modesEvent = kind => e => {
  e.preventDefault()
  storeForm()
  switchMode(kind)
}

const modes = () => {
  const mode = $("#mode")
  const m = mode.val()

  $("#moderesults").off("click").click(modesEvent("results"))
  $("#modepassage").off("click").click(modesEvent("passage"))
  ensureLoaded("passage", "passages", m)
  if (mode.val() == "results") {
    ensureLoaded("sections", null, m)
    ensureLoaded("tuples", null, m)
    ensureLoaded("query", "pages", m)
  }
}

// switch to passage mode after clicking on a result

const switchEvent = e => {
  e.preventDefault()
  const { currentTarget } = e
  const seq = $(currentTarget).closest("details").attr("seq")
  $("#mode").val("passages")
  $("#sec0").val($(currentTarget).attr("sec0"))
  $("#sec1").val($(currentTarget).attr("sec1"))
  $("#sec2").val($(currentTarget).attr("sec2"))
  $("#pos").val(seq)
  storeForm()
  getTable("passage", "passages", "passage")
}

const switchPassage = () => {
  $(".pq").off("click").click(switchEvent)
}

/* tables: getting tabular data from the server
 *
 */

const ensureLoaded = (kind, subkind, m) => {
  const table = $(`#${kind}Table`)
  if (!table.html()) {
    getTable(kind, subkind, m)
  } else {
    switchMode(m)
  }
}

const getTable = (kind, subkind, m, button) => {
  const url = `/${kind}`
  const destTable = $(`#${kind}Table`)
  const destMsg = $(`#${kind}Messages`)
  const destSub = $(`#${subkind}`)
  const nresults = $(".nresults")
  const go = document.querySelector("form")
  const formData = new FormData(go)
  if (button) {
    button.addClass("fa-spin")
  }
  if (kind == "query") {
    nresults.html("...")
  }
  $.ajax({
    type: "POST",
    url,
    data: formData,
    processData: false,
    contentType: false,
    success: data => {
      const { table = "", messages = "", nResults = 0 } = data
      destTable.html(table)
      if (kind == "query") {
        nresults.html(nResults)
      }
      destMsg.html(messages)
      if (subkind != null) {
        const subs = data[subkind]
        if (subs) {
          destSub.html(subs)
          subLinks(kind, subkind)
          if (subkind == "passages") {
            filterS0()
          }
        }
      }
      const { features } = data
      if (features != null) {
        $("#features").val(features)
      }
      if (button) {
        button.removeClass("fa-spin")
      }
      switchPassage()
      details(kind)
      sections()
      tuples()
      nodes()
      switchMode(m)
      storeForm()
      gotoFocus(kind)
      mathTypeset(destTable)
      activateEdges()
    },
  })
}

const gotoFocus = kind => {
  if (kind == "passage" || kind == "query") {
    const rTarget = $(`#${kind}Table details.focus`)
    if (rTarget != null && rTarget[0] != null) {
      rTarget[0].scrollIntoView(false)
    }
  }
}

const activateTables = (kind, subkind) => {
  const button = $(`#${kind}Go`)
  const passButton = button.find("span")
  button.off("click").click(e => {
    e.preventDefault()
    storeForm()
    let m = $("#mode").val()
    if (kind == "passage" && m != "passage") {
      m = "passage"
    } else if (kind != "passage" && m != "results") {
      m = "results"
    }
    getTable(kind, subkind, m, passButton)
  })
  detailc(kind)
  const xpa = adjustOpened(kind)
  detailSet(kind, xpa)
}

// navigation links through passages and results

const subLinks = (kind, subkind) => {
  if (subkind == "pages") {
    $(".pnav")
      .off("click")
      .click(e => {
        e.preventDefault()
        const { currentTarget } = e
        $("#pos").val($(currentTarget).text())
        storeForm()
        getTable(kind, subkind, "results")
      })
  } else if (subkind == "passages") {
    const opKey = `${kind}Op`
    $(".s0nav")
      .off("click")
      .click(e => {
        e.preventDefault()
        const { currentTarget } = e
        $("#sec0").val($(currentTarget).text())
        $("#sec1").val("1")
        $("#sec2").val("")
        $(`#${opKey}`).val("")
        storeForm()
        getTable(kind, subkind, "passages")
      })
    $(".s1nav")
      .off("click")
      .click(e => {
        e.preventDefault()
        const { currentTarget } = e
        $("#sec1").val($(currentTarget).text())
        $("#sec2").val("")
        $(`#${opKey}`).val("")
        storeForm()
        getTable(kind, subkind, "passages")
      })
  }
}

// controlling the "open all" checkbox

const detailc = kind => {
  $(`#${kind}Expac`)
    .off("click")
    .click(e => {
      e.preventDefault()
      const expa = $(`#${kind}Expa`)
      const xpa = expa.val()
      const newXpa = xpa == "1" ? "-1" : xpa == "-1" ? "1" : xpa == "0" ? "-1" : "-1"
      detailSet(kind, newXpa)
      const dPretty = $(`#${kind}Table details.pretty`)
      if (newXpa == "-1") {
        dPretty.each((i, elem) => {
          const el = $(elem)
          if (el.prop("open")) {
            el.prop("open", false)
          }
        })
      } else if (newXpa == "1") {
        dPretty.each((i, elem) => {
          const el = $(elem)
          if (!el.prop("open")) {
            el.prop("open", true)
          }
        })
      }
    })
}

const detailSet = (kind, xpa) => {
  const expac = $(`#${kind}Expac`)
  const expa = $(`#${kind}Expa`)
  const curVal = xpa == null ? expa.val() : xpa
  if (curVal == "-1") {
    expa.val("-1")
    expac.prop("checked", false)
    expac.prop("indeterminate", false)
  } else if (curVal == "1") {
    expa.val("1")
    expac.prop("checked", true)
    expac.prop("indeterminate", false)
  } else if (curVal == "0") {
    expa.val("0")
    expac.prop("checked", false)
    expac.prop("indeterminate", true)
  } else {
    expa.val("-1")
    expac.prop("checked", false)
    expac.prop("indeterminate", false)
  }
  const op = $(`#${kind}Op`)
  if (curVal == "-1") {
    op.val("")
  } else if (curVal == "1") {
    const dPretty = $(`#${kind}Table details.pretty`)
    const allNumbers = dPretty.map((i, elem) => $(elem).attr("seq")).get()
    op.val(allNumbers.join(","))
  }
  storeForm()
}

const adjustOpened = kind => {
  const openedElem = $(`#${kind}Op`)
  const dPretty = $(`#${kind}Table details.pretty`)
  const openedDetails = dPretty.filter((i, elem) => elem.open)
  const closedDetails = dPretty.filter((i, elem) => !elem.open)
  const openedNumbers = openedDetails.map((i, elem) => $(elem).attr("seq")).get()
  const closedNumbers = closedDetails.map((i, elem) => $(elem).attr("seq")).get()

  const currentOpenedStr = openedElem.val()
  const currentOpened = currentOpenedStr == "" ? [] : currentOpenedStr.split(",")
  const reduceOpened = currentOpened.filter(
    n => closedNumbers.indexOf(n) < 0 && openedNumbers.indexOf(n) < 0
  )
  const newOpened = reduceOpened.concat(openedNumbers)
  openedElem.val(newOpened.join(","))
  const nOpen = openedDetails.length
  const nClosed = closedDetails.length
  const xpa = nOpen == 0 ? "-1" : nClosed == 0 ? "1" : "0"
  return xpa
}

// opening and closing details in a table

const details = kind => {
  const details = $(`#${kind}Table details.pretty`)
  details.on("toggle", e => {
    const { currentTarget } = e
    const xpa = adjustOpened(kind)
    detailSet(kind, xpa)
    if ($(currentTarget).prop("open") && !$(currentTarget).find("div.pretty").html()) {
      getOpen(kind, $(currentTarget))
    }
  })
}

const getOpen = (kind, elem) => {
  const seq = elem.attr("seq")
  const url = `/${kind}/${seq}`
  const dest = elem.find("div.pretty")
  const go = document.querySelector("form")
  const formData = new FormData(go)
  $.ajax({
    type: "POST",
    url,
    data: formData,
    processData: false,
    contentType: false,
    success: data => {
      const { table } = data
      dest.html(table)
      mathTypeset(dest)
      activateEdges()
    },
  })
}

/* auto submit data request after interacting with a control
 *
 */

const reactive = () => {
  const form = $("form")
  $(".r").change(() => {
    form.submit()
  })
  $("textarea").change(() => {
    storeForm()
  })
  $("input").change(() => {
    storeForm()
  })
}

const cradios = () => {
  $(".cradio").change(() => {
    $("#cond").prop("checked", true)
  })
}

/* color map handling
 *
 */

const colorMap = () => {
  const form = $("form")
  const colorMapN = $('input[name="colormapn"]')

  $("#colormapplus")
    .off("click")
    .click(e => {
      e.preventDefault()
      const cn = parseInt(colorMapN.val())
      colorMapN.val(cn + 1)
      storeForm()
      form.submit()
    })
  $("#colormapmin")
    .off("click")
    .click(e => {
      e.preventDefault()
      const cn = parseInt(colorMapN.val())
      colorMapN.val(cn > 0 ? cn - 1 : 0)
      storeForm()
      form.submit()
    })
  $(".clmap").change(() => {
    storeForm()
    form.submit()
  })
}

const eColorMap = () => {
  const form = $("form")

  $(".ecolormapmin")
    .off("click")
    .click(e => {
      e.preventDefault()
      const { currentTarget } = e
      const elem = $(currentTarget)
      const pos = elem.attr("pos")
      $(`input[name="edge_name_${pos}"]`).val("")

      storeForm()
      form.submit()
    })
  $(".eclmap").change(() => {
    storeForm()
    form.submit()
  })
}

const activateEdges = () => {
  const form = $("form")

  $('.etf')
    .off("click")
    .click(e => {
      e.preventDefault()
      const { currentTarget } = e
      const elem = $(currentTarget)
      const ef = elem.attr("ef")
      const nd = elem.attr("nd")
      const md = elem.attr("md")
      const arrow = elem.attr("arrow")
      let f
      let t
      if (arrow == "right") {
        f = parseInt(nd)
        t = parseInt(md)
      }
      else {
        t = parseInt(nd)
        f = parseInt(md)
      }
      for (let p = 1; p <= 3; p++) {
        const fRep = p == 1 ? f : p == 2 ? "any" : f
        const tRep = p == 1 ? "any" : p == 2 ? t : t
        $(`input[name="edge_name_new_${p}"]`).val(ef)
        $(`input[name="edge_from_new_${p}"]`).val(fRep)
        $(`input[name="edge_to_new_${p}"]`).val(tRep)
      }
      storeForm()
      form.submit()
    })
}

/* controlling the filtering of the section list
 *
 */

const filterS0 = () => {
  const filterControl = $("#s0filter")
  const filterTotal = $("#s0total")
  const s0items = $(".s0nav")
  const total = s0items.length

  const applyFilter = filterValueRaw => {
    const filterValue = filterValueRaw.toLowerCase()
    let s = 0
    s0items.each((i, elem) => {
      const el = $(elem)
      const s0 = el.text().toLowerCase()
      if (filterValue == "" || s0.indexOf(filterValue) >= 0) {
        el.show()
        s += 1
      } else {
        el.hide()
      }
    })
    const totalRep = total == s ? `${total}` : `${s} of ${total}`
    filterTotal.html(totalRep)
  }

  filterControl.on("input", e => {
    e.preventDefault()
    const filterValue = e.target.value.toLowerCase()
    applyFilter(filterValue)
    storeForm()
  })

  applyFilter(filterControl.val())
}

/* controlling the side bar
 *
 */

const sidebar = () => {
  const side = $("#side")
  const sideStr = side.val()
  const parts = new Set(sideStr ? sideStr.split(",") : [])
  const headers = $("#sidebar div").filter(
    (i, elem) => $(elem).attr("status") != "about"
  )
  const bodies = $("#sidebarcont div").filter(
    (i, elem) => $(elem).attr("status") != "about"
  )
  headers.each((i, elem) => {
    const el = $(elem)
    const part = el.attr("status")
    if (parts.has(part)) {
      el.addClass("active")
    } else {
      el.removeClass("active")
    }
  })
  bodies.each((i, elem) => {
    const el = $(elem)
    const part = el.attr("status")
    if (parts.has(part)) {
      el.addClass("active")
    } else {
      el.removeClass("active")
    }
  })
  $("#sidebar a")
    .off("click")
    .click(e => {
      e.preventDefault()
      const { currentTarget } = e
      const header = $(currentTarget).closest("div")
      const part = header.attr("status")
      const side = $("#side")
      const sideStr = side.val()
      const parts = new Set(sideStr ? sideStr.split(",") : [])
      const body = $(`#sidebarcont div[status="${part}"]`)
      const isActive = header.hasClass("active")
      if (isActive) {
        header.removeClass("active")
        body.removeClass("active")
        parts.delete(part)
        side.val("")
      } else {
        header.addClass("active")
        body.addClass("active")
        parts.add(part)
      }
      side.val(Array.from(parts).join(","))
      storeForm()
    })
}

const doDstate = () => {
  const dstate = $("#dstate")
  const expandedStr = dstate.val()
  const dOpened = expandedStr == "" ? [] : expandedStr.split(",")
  for (const dId of dOpened) {
    const details = $(`#${dId}`)
    details.prop("open", true)
  }
  $("details.dstate").on("toggle", e => {
    const { currentTarget } = e
    const dStates = $("details.dstate")
    const op = $("#dstate")
    const thisState = $(currentTarget)
    const thisId = thisState.attr("id")
    const thisOpen = thisState.prop("open")
    const expandedDetails = dStates
      .filter((i, elem) => $(elem).prop("open") && $(elem).attr("id") != thisId)
      .map((i, elem) => $(elem).attr("id"))
      .get()
    if (thisOpen) {
      expandedDetails.push(thisId)
    }
    op.val(expandedDetails.join(","))
  })
}

/* controlling the textarea pads
 * Clicking on certain elements in the table rows will
 * populate the pads
 */

const sectionsEvent = e => {
  const elems = $("#sections")
  e.preventDefault()
  e.stopPropagation()
  const { currentTarget } = e
  const txt = $(currentTarget).attr("sec")
  const orig = elems.val()
  elems.val(`${orig}\n${txt}`)
}

const sections = () => {
  $(".rwh").off("click").click(sectionsEvent)
}

const tuplesEvent = e => {
  const elems = $("#tuples")
  e.preventDefault()
  e.stopPropagation()
  const { currentTarget } = e
  const txt = $(currentTarget).attr("tup")
  const orig = elems.val()
  elems.val(`${orig}\n${txt}`)
}

const tuples = () => {
  $(".sq").off("click").click(tuplesEvent)
}

const nodesEvent = e => {
  const elems = $("#tuples")
  e.preventDefault()
  e.stopPropagation()
  const { currentTarget } = e
  const txt = $(currentTarget).text()
  const orig = elems.val()
  elems.val(`${orig}\n${txt}`)
}

const nodes = () => {
  $(".nd").off("click").click(nodesEvent)
}

/* job control
 *
 */

const verifyApp = (jobContent, app) => {
  const { appName } = jobContent
  if (appName == app) {
    return true
  }
  if (confirm(`Change app "${appName}" to "${app}" ?`)) {
    jobContent["appName"] = app
    return true
  }
  return false
}

const suggestName = (jobName, other) => {
  const jobs = getJobs()
  let newName = jobName
  const resolved = s => s != "" && (!other || s != jobName) && !jobs.has(s)
  let cancelled = false
  while (!resolved(newName) && !cancelled) {
    while (!resolved(newName)) {
      newName += "N"
    }
    const answer = prompt("New job name:", newName)
    if (answer == null) {
      cancelled = true
    } else {
      newName = answer
    }
  }
  return cancelled ? null : newName
}

const jobOptions = () => {
  const jChange = $("#jchange")
  const jobh = $("#jobh")
  const currentJob = jobh.val()
  let html = ""
  for (const job of getJobs()) {
    const selected = job == currentJob ? " selected" : ""
    html += `<option value="${job}"${selected}>${job}</option>`
    jChange.html(html)
  }
}

const jobControls = () => {
  const jChange = $("#jchange")
  const jClear = $("#jclear")
  const jDelete = $("#jdelete")
  const jRename = $("#jrename")
  const jNew = $("#jnew")
  const jDup = $("#jdup")
  const jOpen = $("#jopen")
  const jFile = $("#jfile")
  const jMeta = $("#jmeta")
  const aName = $("#appName")
  const metaDiv = $("#exportmeta")
  const metaOpen = $("#jmetaopen")

  const form = $("form")
  const jobh = $("#jobh")

  const isOpen = metaOpen.val() == "v"
  if (isOpen) {
    metaDiv.show()
  }
  else {
    metaDiv.hide()
  }

  jChange.change(e => {
    const oldJob = jobh.val()
    const newJob = e.target.value
    if (oldJob == newJob) {
      return
    }
    storeForm()
    setLastJob($("#appName").val(), newJob)
    jobh.val(e.target.value)
    readForm()
    form.submit()
  })

  jClear.off("click").click(() => {
    const jobName = jobh.val()
    if (confirm(`Reset job ${jobName}?`)) {
      clearForm()
      storeForm()
      setLastJob($("#appName").val(), $("#jobh").val())
      form.submit()
    }
  })

  jDelete.off("click").click(() => {
    const jobName = jobh.val()
    if (confirm(`Delete job ${jobName}?`)) {
      setLastJob($("#appName").val(), "")
      deleteForm()
      jobh.val("")
      clearForm()
    }
  })

  jRename.off("click").click(e => {
    const jobName = jobh.val()
    const newName = suggestName(jobName, true)
    if (newName == null) {
      e.preventDefault()
      return
    }
    deleteForm()
    jobh.val(newName)
    storeForm()
    setLastJob($("#appName").val(), $("#jobh").val())
  })

  jOpen.off("click").click(e => {
    jFile.click()
    e.preventDefault()
  })
  jFile.change(() => {
    const jobFile = jFile.prop("files")[0]
    const reader = new FileReader()
    reader.onload = e => {
      const jobContent = JSON.parse(e.target.result)
      if (!verifyApp(jobContent, aName.val())) {
        e.preventDefault()
        return
      }
      const newName = suggestName(jobContent.jobName, false)
      if (newName == null) {
        e.preventDefault()
        return
      }
      storeForm()
      jobContent["jobName"] = newName
      readForm(jobContent)
      setLastJob($("#appName").val(), $("#jobh").val())
      form.submit()
    }
    reader.readAsText(jobFile)
  })

  jNew.off("click").click(e => {
    const jobName = jobh.val()
    const newName = suggestName(jobName, true)
    if (newName == null) {
      e.preventDefault()
      return
    }
    storeForm()
    clearForm()
    jobh.val(newName)
    setLastJob($("#appName").val(), $("#jobh").val())
    storeForm()
  })

  jDup.off("click").click(e => {
    const jobName = jobh.val()
    const newName = suggestName(jobName, true)
    if (newName == null) {
      e.preventDefault()
      return
    }
    storeForm()
    jobh.val(newName)
    setLastJob($("#appName").val(), $("#jobh").val())
    storeForm()
  })

  jMeta.off("click").click(e => {
    e.preventDefault()
    metaDiv.toggle()
    const isOpen = metaOpen.val() == "v"
    metaOpen.val(isOpen ? "x" : "v")
  })
}

const readForm = jobContent => {
  let formObj
  const go = document.querySelector("form")
  if (jobContent == null) {
    const formData = new FormData(go)
    const appName = formData.get("appName")
    const jobName = formData.get("jobName")
    const formKey = `tf/${appName}/${jobName}`
    const formStr = localStorage.getItem(formKey)
    formObj = JSON.parse(formStr)
  } else {
    formObj = jobContent
  }
  const form = $("#go")
  for (const [key, value] of Object.entries(formObj)) {
    let iElem = $(`[name="${key}"]`)
    if (iElem.length == 0) {
      form.prepend(`<input type="hidden" name="${key}" value="${value}">`)
      iElem = $(`[name="${key}"]`)
    }
    iElem.val(value)
  }
}

const clearForm = () => {
  $("#resetf").val("1")
}

const deleteForm = () => {
  const go = document.querySelector("form")
  const formData = new FormData(go)
  const appName = formData.get("appName")
  const jobName = formData.get("jobName")
  const formKey = `tf/${appName}/${jobName}`
  localStorage.removeItem(formKey)
}

const storeForm = () => {
  const go = document.querySelector("form")
  const formData = new FormData(go)
  const formObj = {}
  for (const [key, value] of formData) {
    formObj[key] = value
  }
  const formStr = JSON.stringify(formObj)
  const appName = formData.get("appName")
  const jobName = formData.get("jobName")
  const formKey = `tf/${appName}/${jobName}`
  localStorage.setItem(formKey, formStr)
}

const getJobs = () => {
  const go = document.querySelector("form")
  const formData = new FormData(go)
  const appName = formData.get("appName")
  const tfPrefix = `tf/${appName}/`
  const tfLength = tfPrefix.length
  return new Set(
    Object.keys(localStorage)
      .filter(key => key.startsWith(tfPrefix))
      .map(key => key.substring(tfLength))
  )
}

const setLastJob = (appName, jobName) => {
  const lastJob = localStorage.getItem(lastJobKey)
  const lastJobData = lastJob ? JSON.parse(lastJob) : {}
  lastJobData[appName] = jobName
  localStorage.setItem(lastJobKey, JSON.stringify(lastJobData))
}

const getLastJob = appName => {
  const lastJob = localStorage.getItem(lastJobKey)
  const lastJobData = lastJob ? JSON.parse(lastJob) : {}
  const { [appName]: lastJobName } = lastJobData
  return lastJobName == null ? "default" : lastJobName
}

const initForm = () => {
  const loadJob = $("#jobl")
  if (loadJob.val() == "1") {
    loadJob.val("")
    const appName = $("#appName").val()
    const lastJobName = getLastJob(appName)
    const jobContent = localStorage.getItem(`tf/${appName}/${lastJobName}`)
    if (jobContent) {
      readForm(JSON.parse(jobContent))
      $("form").submit()
    }
  } else {
    storeForm()
  }
}

/* main
 *
 */

$(window).on("load", () => {
  initForm()
  sidebar()
  modes()
  activateTables("sections", null)
  activateTables("tuples", null)
  activateTables("query", "pages")
  activateTables("passage", "passages")
  cradios()
  colorMap()
  eColorMap()
  doDstate()
  reactive()
  jobOptions()
  jobControls()
  initAIQueryGenerator()
  initChat()
})

/* AI Query Generator
 *
 */

const AI_PROVIDERS = {
  gemini: {
    label: "Gemini",
    storage: "tf_gemini_api_key",
    placeholder: "Gemini API Key",
    keyUrl: "https://aistudio.google.com/",
    baseUrlHint: "https://generativelanguage.googleapis.com",
  },
  claude: {
    label: "Claude",
    storage: "tf_anthropic_api_key",
    placeholder: "Anthropic API Key",
    keyUrl: "https://console.anthropic.com/settings/keys",
    baseUrlHint: "https://api.anthropic.com",
  },
}

const AI_PROVIDER_STORAGE = "tf_ai_provider"
const aiSettingKey = (provider, field) => `tf_ai_${provider}_${field}`

const initAIQueryGenerator = () => {
  const generateBtn = $("#generateQuery")
  const aiPrompt = $("#aiPrompt")
  const apiKey = $("#apiKey")
  const aiModel = $("#aiModel")
  const aiBaseUrl = $("#aiBaseUrl")
  const providerSel = $("#aiProvider")
  const aiStatus = $("#aiStatus")
  const aiExplanation = $("#aiExplanation")
  const queryTextarea = $("#query")
  const apiKeyHelper = $("#apiKeyHelper")
  const apiKeyLink = $("#apiKeyLink")

  const currentProvider = () => providerSel.val() || "gemini"

  /* Load the saved key/model/base url for the selected provider into the
   * form, and point the help link at that provider's console.
   */
  const loadProviderSettings = announce => {
    const provider = currentProvider()
    const spec = AI_PROVIDERS[provider]
    const key = localStorage.getItem(spec.storage) || ""
    apiKey.val(key)
    apiKey.attr("placeholder", spec.placeholder)
    aiModel.val(localStorage.getItem(aiSettingKey(provider, "model")) || "")
    aiBaseUrl.val(localStorage.getItem(aiSettingKey(provider, "baseurl")) || "")
    aiBaseUrl.attr("placeholder", `API base URL (default: ${spec.baseUrlHint})`)
    apiKeyLink.attr("href", spec.keyUrl)
    apiKeyLink.html(`Get a ${spec.label} API key here`)
    if (key) {
      apiKeyHelper.hide()
      if (announce) {
        aiStatus.html(
          `<span class="info">🔑 ${spec.label} key loaded from browser storage</span>`
        )
      }
    } else {
      /* The helper link already prompts for a key; no status line too. */
      apiKeyHelper.show()
      if (announce) {
        aiStatus.html("")
      }
    }
    console.log(`[AI] provider=${provider} hasKey=${!!key}`)
  }

  providerSel.val(localStorage.getItem(AI_PROVIDER_STORAGE) || "gemini")
  loadProviderSettings(true)

  providerSel.off("change").change(() => {
    localStorage.setItem(AI_PROVIDER_STORAGE, currentProvider())
    loadProviderSettings(true)
    apiKey.focus()
  })

  /* Alt+P cycles providers from anywhere in the AI section. */
  $("#aiQueryGenerator").off("keydown.provider").on("keydown.provider", e => {
    if (e.altKey && (e.key == "p" || e.key == "P")) {
      e.preventDefault()
      providerSel.val(currentProvider() == "gemini" ? "claude" : "gemini")
      providerSel.trigger("change")
    }
  })

  apiKey.off("input").on("input", () => {
    const spec = AI_PROVIDERS[currentProvider()]
    const key = apiKey.val().trim()
    if (key) {
      localStorage.setItem(spec.storage, key)
      apiKeyHelper.hide()
    } else {
      localStorage.removeItem(spec.storage)
      apiKeyHelper.show()
    }
  })

  const persistSetting = (elem, field) => {
    elem.off("input").on("input", () => {
      const value = elem.val().trim()
      const storeKey = aiSettingKey(currentProvider(), field)
      if (value) {
        localStorage.setItem(storeKey, value)
      } else {
        localStorage.removeItem(storeKey)
      }
    })
  }
  persistSetting(aiModel, "model")
  persistSetting(aiBaseUrl, "baseurl")

  const clearBtn = $("#clearApiKey")
  clearBtn.off("click").click(e => {
    e.preventDefault()
    const spec = AI_PROVIDERS[currentProvider()]
    if (confirm(`Clear saved ${spec.label} API key from browser storage?`)) {
      localStorage.removeItem(spec.storage)
      apiKey.val("")
      apiKeyHelper.show()
      aiStatus.html(
        `<span class="info">🗑️ ${spec.label} API key cleared from storage</span>`
      )
    }
  })

  const runGeneration = async () => {
    const prompt = aiPrompt.val().trim()
    const key = apiKey.val().trim()
    const provider = currentProvider()
    const spec = AI_PROVIDERS[provider]

    aiStatus.html("")
    aiExplanation.html("")

    if (!prompt) {
      aiStatus.html(
        '<span class="error">⚠️ Please enter a description of what you want to search for</span>'
      )
      aiPrompt.focus()
      return
    }
    if (!key) {
      aiStatus.html(
        `<span class="error">⚠️ Please enter your ${spec.label} API key</span>`
      )
      apiKey.focus()
      return
    }

    generateBtn.prop("disabled", true)
    generateBtn.html('<span class="fa fa-spinner fa-spin"></span> Generating...')
    aiStatus.html(
      `<span class="info">🤖 Generating query with ${spec.label}...</span>`
    )
    console.log(`[AI] generating: provider=${provider} prompt=${prompt}`)

    try {
      const response = await fetch("/ai/generate_query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          prompt,
          api_key: key,
          provider,
          model: aiModel.val().trim(),
          base_url: aiBaseUrl.val().trim(),
        }),
      })

      const responseText = await response.text()
      let data
      try {
        data = JSON.parse(responseText)
      } catch (parseError) {
        aiStatus.html(
          `<span class="error">❌ Server returned invalid response: ${responseText.substring(
            0,
            200
          )}</span>`
        )
        return
      }

      console.log("[AI] response", data)

      if (!response.ok || data.error) {
        aiStatus.html(
          `<span class="error">❌ Error: ${data.error || "Unknown error"}</span>`
        )
        return
      }

      queryTextarea.val(data.query)
      const countMsg =
        data.result_count == null
          ? ""
          : data.result_count == 0
          ? " — but it matches nothing in the corpus"
          : ` — ${data.result_count} results`
      aiStatus.html(
        `<span class="success">✅ Query generated${countMsg}</span>`
      )
      if (data.explanation) {
        aiExplanation.html(`<span class="info">💡 ${data.explanation}</span>`)
      }
      storeForm()
    } catch (error) {
      aiStatus.html(`<span class="error">❌ Network error: ${error.message}</span>`)
    } finally {
      generateBtn.prop("disabled", false)
      generateBtn.html("Generate Query")
    }
  }

  generateBtn.off("click").click(e => {
    e.preventDefault()
    runGeneration()
  })

  /* Ctrl/Cmd+Enter in the prompt box submits. */
  aiPrompt.off("keydown").on("keydown", e => {
    if ((e.ctrlKey || e.metaKey) && e.key == "Enter") {
      e.preventDefault()
      runGeneration()
    }
  })
}

/* Research chat
 *
 * Streams an agent turn from /ai/chat as server-sent events, rendering
 * each Text-Fabric tool call as a collapsible row so every search behind
 * an answer is inspectable — and loadable straight into the search pad.
 */

const CHAT_CONV_STORAGE = "tf_chat_conv_id"

const chatEscape = text =>
  String(text == null ? "" : text)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")

/* Deliberately small markdown subset: enough for the agent's answers
 * (bold, code, headings, lists, paragraphs) without pulling in a library.
 * Everything is escaped first, so this never renders raw HTML.
 */
const chatMarkdown = text => {
  const escaped = chatEscape(text)
  const lines = escaped.split("\n")
  const out = []
  let inList = false
  let inCode = false
  const closeList = () => {
    if (inList) {
      out.push("</ul>")
      inList = false
    }
  }
  for (const line of lines) {
    if (/^\s*```/.test(line)) {
      if (inCode) {
        out.push("</code></pre>")
        inCode = false
      } else {
        closeList()
        out.push("<pre class='chat-code'><code>")
        inCode = true
      }
      continue
    }
    if (inCode) {
      out.push(line + "\n")
      continue
    }
    const heading = line.match(/^(#{1,4})\s+(.*)$/)
    if (heading) {
      closeList()
      const level = Math.min(6, heading[1].length + 2)
      out.push(`<h${level}>${heading[2]}</h${level}>`)
      continue
    }
    const item = line.match(/^\s*[-*]\s+(.*)$/)
    if (item) {
      if (!inList) {
        out.push("<ul>")
        inList = true
      }
      out.push(`<li>${item[1]}</li>`)
      continue
    }
    if (!line.trim()) {
      closeList()
      continue
    }
    closeList()
    out.push(`<p>${line}</p>`)
  }
  if (inCode) {
    out.push("</code></pre>")
  }
  closeList()
  return out
    .join("")
    .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
    .replace(/`([^`]+)`/g, "<code>$1</code>")
}

const initChat = () => {
  const panel = $("#chatPanel")
  if (!panel.length) {
    return
  }
  const messages = $("#chatMessages")
  const input = $("#chatInput")
  const sendBtn = $("#chatSend")
  const stopBtn = $("#chatStop")
  const resetBtn = $("#chatReset")
  const status = $("#chatStatus")
  const empty = $("#chatEmpty")

  let convId = localStorage.getItem(CHAT_CONV_STORAGE)
  if (!convId) {
    convId = `c${Date.now()}${Math.floor(Math.random() * 1e6)}`
    localStorage.setItem(CHAT_CONV_STORAGE, convId)
  }
  let controller = null

  /* Only follow the tail when the user is already at the bottom, so
   * scrolling back through a long answer is not yanked away.
   */
  const nearBottom = () => {
    const el = messages.get(0)
    if (!el) {
      return true
    }
    return el.scrollHeight - el.scrollTop - el.clientHeight < 80
  }
  const scrollToEnd = force => {
    const el = messages.get(0)
    if (el && (force || nearBottom())) {
      el.scrollTop = el.scrollHeight
    }
  }

  const addBubble = (role, html) => {
    empty.hide()
    const bubble = $(
      `<div class="chat-msg chat-${role}"><div class="chat-body"></div></div>`
    )
    bubble.find(".chat-body").html(html)
    messages.append(bubble)
    scrollToEnd(role == "user")
    return bubble
  }

  const setBusy = busy => {
    sendBtn.prop("disabled", busy)
    sendBtn.html(busy ? '<span class="fa fa-spinner fa-spin"></span> Working' : "Ask")
    stopBtn.toggle(busy)
    input.prop("disabled", busy)
  }

  /* One tool call: a collapsed status line that expands to show the
   * inputs and the outcome, plus a button to run the query in the pad.
   */
  const addToolRow = event => {
    empty.hide()
    const row = $('<div class="chat-tool" data-tool-id=""></div>')
    row.attr("data-tool-id", event.id)
    const head = $(
      `<button type="button" class="chat-tool-head" aria-expanded="false">
         <span class="chat-tool-icon">⏳</span>
         <span class="chat-tool-title"></span>
         <span class="chat-tool-count"></span>
         <span class="chat-tool-chevron">›</span>
       </button>`
    )
    head.find(".chat-tool-title").text(event.title || event.name)
    const detail = $('<div class="chat-tool-detail" hidden></div>')
    for (const field of event.inputs || []) {
      const line = $('<div class="chat-tool-field"></div>')
      line.append($('<span class="chat-tool-label"></span>').text(`${field.label}: `))
      if (field.label == "Query") {
        line.append($('<pre class="chat-tool-query"></pre>').text(field.value))
      } else {
        line.append($("<span></span>").text(field.value))
      }
      detail.append(line)
    }
    head.off("click").click(() => {
      const open = detail.prop("hidden")
      detail.prop("hidden", !open)
      head.attr("aria-expanded", open ? "true" : "false")
      head.toggleClass("open", open)
      scrollToEnd()
    })
    row.append(head).append(detail)
    messages.append(row)
    scrollToEnd()
    return row
  }

  const completeToolRow = event => {
    const row = messages.find(`.chat-tool[data-tool-id="${event.id}"]`).last()
    if (!row.length) {
      return
    }
    row.find(".chat-tool-icon").text(event.ok ? "✓" : "✕")
    row.toggleClass("failed", !event.ok)
    row.find(".chat-tool-count").text(event.summary || "")
    const detail = row.find(".chat-tool-detail")
    const outcome = $('<div class="chat-tool-outcome"></div>')
    outcome.toggleClass("error", !event.ok)
    outcome.text(event.summary || "")
    detail.append(outcome)

    const rows = ((event.detail || {}).sample || []).slice(0, 6)
    if (rows.length) {
      const list = $('<div class="chat-tool-sample"></div>')
      for (const r of rows) {
        const line = $('<div class="chat-tool-row"></div>')
        line.append($('<span class="chat-ref"></span>').text(r.ref || ""))
        line.append($('<span class="chat-heb"></span>').text((r.words || []).slice(1).join(" ")))
        list.append(line)
      }
      detail.append(list)
    }
    const buckets = ((event.detail || {}).buckets || []).slice(0, 10)
    if (buckets.length) {
      const list = $('<div class="chat-tool-sample"></div>')
      for (const b of buckets) {
        list.append(
          $('<div class="chat-tool-row"></div>').text(
            `${b.value} — ${b.count} (${b.percent}%)`
          )
        )
      }
      detail.append(list)
    }
    const errors = (event.detail || {}).errors
    if (errors) {
      detail.append($('<div class="chat-tool-outcome error"></div>').text(errors))
    }

    if (event.template) {
      const load = $(
        '<button type="button" class="small chat-load">Load into search pad</button>'
      )
      load.off("click").click(() => {
        $("#query").val(event.template)
        storeForm()
        getTable("query", "results", "results")
        status.text("Loaded into the search pad")
        const pad = $("#query").get(0)
        if (pad && pad.scrollIntoView) {
          pad.scrollIntoView({ block: "center", behavior: "smooth" })
        }
      })
      detail.append(load)
    }
  }

  const providerSettings = () => {
    const provider = localStorage.getItem(AI_PROVIDER_STORAGE) || "gemini"
    const spec = AI_PROVIDERS[provider]
    return {
      provider,
      api_key: localStorage.getItem(spec.storage) || "",
      model: localStorage.getItem(aiSettingKey(provider, "model")) || "",
      base_url: localStorage.getItem(aiSettingKey(provider, "baseurl")) || "",
    }
  }

  const ask = async question => {
    const settings = providerSettings()
    if (!settings.api_key) {
      status.html(
        '<span class="error">Enter an API key in the AI Query Generator first</span>'
      )
      return
    }
    addBubble("user", chatEscape(question))
    input.val("")
    setBusy(true)
    status.text("Thinking…")
    console.log(`[chat] asking via ${settings.provider}: ${question}`)

    controller = new AbortController()
    let answerBubble = null
    try {
      const response = await fetch("/ai/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question, conv_id: convId, ...settings }),
        signal: controller.signal,
      })
      if (!response.ok) {
        let message = `HTTP ${response.status}`
        try {
          const data = await response.json()
          message = data.error || message
        } catch (e) {
          /* non-JSON error body */
        }
        status.html(`<span class="error">${chatEscape(message)}</span>`)
        return
      }
      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ""
      for (;;) {
        const { done, value } = await reader.read()
        if (done) {
          break
        }
        buffer += decoder.decode(value, { stream: true })
        const chunks = buffer.split("\n\n")
        buffer = chunks.pop()
        for (const chunk of chunks) {
          const line = chunk.trim()
          if (!line.startsWith("data:")) {
            continue
          }
          let event
          try {
            event = JSON.parse(line.slice(5).trim())
          } catch (e) {
            console.warn("[chat] bad event", line)
            continue
          }
          console.log("[chat] event", event)
          if (event.type == "status") {
            status.text(event.phase == "thinking" ? "Thinking…" : event.phase)
          } else if (event.type == "tool_call") {
            status.text("Searching the corpus…")
            addToolRow(event)
          } else if (event.type == "tool_result") {
            completeToolRow(event)
          } else if (event.type == "note") {
            addBubble("note", chatMarkdown(event.text))
          } else if (event.type == "text") {
            answerBubble = addBubble("assistant", chatMarkdown(event.delta))
          } else if (event.type == "error") {
            status.html(`<span class="error">${chatEscape(event.message)}</span>`)
          } else if (event.type == "done") {
            const calls = event.tool_calls
            status.text(
              `${calls} search${calls == 1 ? "" : "es"} · ${event.seconds}s · ${event.provider}`
            )
          }
        }
      }
    } catch (e) {
      if (e.name == "AbortError") {
        status.text("Stopped")
      } else {
        status.html(`<span class="error">${chatEscape(e.message)}</span>`)
      }
    } finally {
      controller = null
      setBusy(false)
      if (answerBubble) {
        scrollToEnd()
      }
    }
  }

  const submit = () => {
    const question = input.val().trim()
    if (!question) {
      input.focus()
      return
    }
    ask(question)
  }

  sendBtn.off("click").click(e => {
    e.preventDefault()
    submit()
  })

  stopBtn.off("click").click(e => {
    e.preventDefault()
    if (controller) {
      controller.abort()
    }
  })

  /* Enter sends, Shift+Enter makes a newline. */
  input.off("keydown").on("keydown", e => {
    if (e.key == "Enter" && !e.shiftKey) {
      e.preventDefault()
      submit()
    }
  })

  $(".chat-suggestion")
    .off("click")
    .click(e => {
      e.preventDefault()
      ask($(e.currentTarget).text().trim())
    })

  resetBtn.off("click").click(async e => {
    e.preventDefault()
    const previous = convId
    convId = `c${Date.now()}${Math.floor(Math.random() * 1e6)}`
    localStorage.setItem(CHAT_CONV_STORAGE, convId)
    messages.find(".chat-msg, .chat-tool").remove()
    empty.show()
    status.text("")
    try {
      await fetch("/ai/chat/reset", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ conv_id: previous }),
      })
    } catch (err) {
      /* the server forgets on restart anyway */
    }
  })
}
