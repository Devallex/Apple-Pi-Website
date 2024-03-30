Array.prototype.slice.call(document.getElementsByTagName("footer")).forEach((footer) => {
	const textContent = footer.textContent
	footer.innerHTML = `
		<div class="background"></div>
		<div class="content">
			${textContent}
			<h1>Find Us</h1>
			<address>
				<h2>Contact</h2>
				<p>
					<a href="mailto:${CONTACT_EMAIL}">${CONTACT_EMAIL}</a>
				</p>
				<h2>Social Media</h2>
				<p>
					<a href="https://www.facebook.com/people/Apple-Pi-Robotics-FRC-Team-2067/100054299360253/">Facebook</a
					<br>
					<a href="https://www.twitter.com/FRC2067">Twitter</a
					<br>
				</p>
				<h2>Address</h2>
				29 Soundview Rd.
				<br>
				Building 2, Unit #3
				<br>
				Guilford, CT 06437
			</address>
		</div>
	`
})

loaded()