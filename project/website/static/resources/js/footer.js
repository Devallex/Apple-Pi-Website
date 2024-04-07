Array.prototype.slice.call(document.getElementsByTagName("footer")).forEach((footer) => {
	const textContent = footer.textContent
	footer.innerHTML = `
		<div class="background"></div>
		<div class="content center">
			${textContent}
			<address>
				<p>
					<label>Contact:</label>
					<a href="mailto:${CONTACT_EMAIL}">${CONTACT_EMAIL}</a>
				</p>
				<p>
					<label>Social Media:</label>
					<a href="https://www.facebook.com/people/Apple-Pi-Robotics-FRC-Team-2067/100054299360253/">Facebook</a> |
					<a href="https://www.twitter.com/FRC2067">Twitter</a>
				</p>
				<p>
					<label>Address:</label>
					29 Soundview Rd.
					Building 2, Unit #3
					Guilford, CT 06437
				</p>
			</address>
		</div>
	`
})

loaded()