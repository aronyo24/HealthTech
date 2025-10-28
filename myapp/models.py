from django.db import models


class ContactMessage(models.Model):
	"""Stores contact form submissions from the HealthTech website."""

	name = models.CharField(max_length=120)
	email = models.EmailField()
	subject = models.CharField(max_length=150)
	message = models.TextField()
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ["-created_at"]
		verbose_name = "Contact message"
		verbose_name_plural = "Contact messages"

	def __str__(self) -> str:  # pragma: no cover - simple display helper
		return f"{self.name} - {self.subject}"
