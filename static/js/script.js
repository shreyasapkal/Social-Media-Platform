
document.addEventListener("DOMContentLoaded", () => {
    const csrfToken = document.querySelector(
        "#post-form [name=csrfmiddlewaretoken]"
    )?.value;

    async function sendRequest(url, options = {}) {
        const response = await fetch(url, {
            ...options,
            headers: {
                "X-CSRFToken": csrfToken,
                ...(options.headers || {})
            }
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || data.message || "Something went wrong.");
        }

        return data;
    }

    // Create a post
    const postForm = document.getElementById("post-form");

    if (postForm) {
        postForm.addEventListener("submit", async (event) => {
            event.preventDefault();

            const button = postForm.querySelector("button[type=submit]");
            const message = document.getElementById("post-message");

            button.disabled = true;
            button.textContent = "Publishing...";

            try {
                const data = await sendRequest(
                    "/api/posts/create/",
                    {
                        method: "POST",
                        body: new FormData(postForm)
                    }
                );

                message.textContent = data.message;
                postForm.reset();
                window.location.reload();
            } catch (error) {
                message.textContent = error.message;
            } finally {
                button.disabled = false;
                button.textContent = "Publish";
            }
        });
    }

    // Like and unlike
    document.querySelectorAll(".like-btn").forEach((button) => {
        button.addEventListener("click", async () => {
            try {
                const data = await sendRequest(button.dataset.url, {
                    method: "POST"
                });

                button.querySelector(".like-count").textContent = data.count;
                button.classList.toggle("liked", data.liked);
            } catch (error) {
                alert(error.message);
            }
        });
    });

    // Delete posts
    document.querySelectorAll(".delete-btn").forEach((button) => {
        button.addEventListener("click", async () => {
            if (!confirm("Are you sure you want to delete this post?")) return;

            try {
                await sendRequest(button.dataset.url, {
                    method: "POST"
                });

                button.closest(".post-card").remove();
            } catch (error) {
                alert(error.message);
            }
        });
    });

    // Add comments
    document.querySelectorAll(".comment-form").forEach((form) => {
        form.addEventListener("submit", async (event) => {
            event.preventDefault();

            const input = form.querySelector("input[name=text]");
            const text = input.value.trim();

            if (!text) return;

            try {
                const data = await sendRequest(form.dataset.url, {
                    method: "POST",
                    body: new URLSearchParams({ text })
                });

                const comments = form.previousElementSibling;
                const comment = document.createElement("div");
                comment.className = "comment";

                const author = document.createElement("strong");
                author.textContent = "@" + data.username;

                comment.append(author, document.createTextNode(" " + data.text));
                comments.appendChild(comment);
                input.value = "";
            } catch (error) {
                alert(error.message);
            }
        });
    });

    // Delete comments
    document.querySelectorAll(".comment-delete").forEach((button) => {
        button.addEventListener("click", async () => {
            try {
                await sendRequest(button.dataset.url, {
                    method: "POST"
                });

                button.closest(".comment").remove();
            } catch (error) {
                alert(error.message);
            }
        });
    });
    document.querySelectorAll(".follow-btn").forEach((button) => {
    button.addEventListener("click", async () => {
        try {
            const data = await sendRequest(button.dataset.url, {
                method: "POST"
            });
            button.textContent = data.following ? "Following" : "Follow";
        } catch (error) {
            alert(error.message);
        }
    });
});
});
