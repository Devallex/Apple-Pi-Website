// https://quilljs.com/docs/guides/cloning-medium-with-parchment

const BlockEmbed = Quill.import('blots/block/embed');

class HighlightBlot extends BlockEmbed {
	static blotName = "embed";
	static tagName = "div";
	static className = "embed";

	static create(value) {
		const node = super.create();

		node.value = value;

		const url = value["url"];
		if (url) {
			node.innerHTML = `<iframe src="${url}"></iframe>`;

			if (url[0] == "/") {
				node.firstChild.onload = () => {
					const innerDocument = node.firstChild.contentDocument;

					for (const header of innerDocument.getElementsByTagName("header")) {
						header.style.display = "none";
					}
					for (const footer of innerDocument.getElementsByTagName("footer")) {
						footer.style.display = "none";
					}
				}
			}
		} else {
			node.innerHTML = `<b>Invalid HTML Embed</b>`;
		}

		return node;
	}

	static value(node) {
		return node.value;
	}

	static formats(node) {
		return node.value;
	}
}
Quill.register(HighlightBlot);

class DividerBlot extends BlockEmbed {
	static blotName = "divider";
	static tagName = "hr";

	static create(value) {
		const node = super.create();

		return node;
	}
}
Quill.register(DividerBlot);