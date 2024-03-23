function createHeaderLink(name, url) {
	if (url == window.location.pathname) {
		name = "<b>" + name + "</b>"
	}

	return `
		<a href=${url}>
			<div>
				${name}
			</div>
		</a>
	`
}

function updateHeader(header, variables) {
	header.innerHTML = `
	<div class="background"></div>
	<div>
		${createHeaderLink("Home", "/")}
		${createHeaderLink("About Us", "/about-us")}
		${createHeaderLink("News & Media", "/news")}
		${createHeaderLink("Our Team", "/users")}
		${createHeaderLink("Documents", "/documents")}
		${createHeaderLink("Log In", "/login")}
	</div>
`
}

Array.prototype.slice.call(document.getElementsByTagName("header")).forEach((header) => {
	updateHeader(header, {})
})

loaded()