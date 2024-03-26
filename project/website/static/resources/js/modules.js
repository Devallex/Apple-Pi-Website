var MODULES = [
	"globals",
	"api",

	"cookies",
	"users",

	"editor",
	"header",
	"footer",
]

modules_script = document.getElementById("modules")

function loaded() {
	loadModule()
}

function getModuleName() {
	if (MODULES.length <= 0) {
		return
	}
	return MODULES.splice(0, 1)[0]
}

function loadScript(path) {
	// var head = document.getElementsByTagName('head')[0]
	var script = document.createElement('script')
	// script.type = 'module'
	script.src = path
	modules_script.parentNode.insertBefore(script, modules_script.nextSibling)
}

var callbacks = []
function onLoaded(callback) {
	callbacks.push(callback)
}

function loadModule() {
	var moduleName = getModuleName()
	if (!moduleName) {
		document.documentElement.style["filter"] = "none"
		callbacks.forEach((callback) => {
			callback()
		})
		return
	}
	loadScript(`/resources/js/${moduleName}.js`)
}

loadModule()