from django.db import models
from users.models import UserProfile
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db.models.signals import post_save
from django.dispatch import receiver


class Category(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Technology(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    category = models.ForeignKey(
        Category, related_name="technologies", on_delete=models.CASCADE
    )
    image = models.ImageField(upload_to="category_images/", blank=True)
    image_name = models.CharField(max_length=100)

    class Meta:
        verbose_name = "Technology"
        verbose_name_plural = "Technologies"

    def __str__(self):
        return self.name


class Module(models.Model):
    title = models.CharField(max_length=100)
    technology = models.ForeignKey(
        Technology, related_name="modules", on_delete=models.CASCADE
    )

    def __str__(self):
        return self.title


class Topic(models.Model):
    title = models.CharField(max_length=100)
    module = models.ForeignKey(Module, related_name="topics", on_delete=models.CASCADE)
    content = models.TextField()

    def __str__(self):
        return self.title


class Question(models.Model):
    DIFFICULTY_CHOICES = [
        ("noob", "Noob"),
        ("junior", "Junior"),
        ("pro", "Pro"),
        ("ninja", "Ninja"),
    ]

    title = models.CharField(max_length=255)
    topic = models.ForeignKey(Topic, related_name="questions", on_delete=models.CASCADE)
    answer = models.TextField(default="No answer provided")
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} - Difficulty: {self.get_difficulty_display()}"


class UserQuestionKnowledge(models.Model):
    KNOWLEDGE_CHOICES = [
        ("good", "Good Knowledge"),
        ("repeat", "Need to Repeat"),
        ("bad", "Bad Knowledge"),
    ]

    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    knowledge_status = models.CharField(max_length=10, choices=KNOWLEDGE_CHOICES)

    class Meta:
        unique_together = ("user", "question")

    def __str__(self):
        return f"{self.user} - {self.question.title} - {self.knowledge_status}"


class UserTechnologyProgress(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    technology = models.ForeignKey(Technology, on_delete=models.CASCADE)
    progress_percentage = models.IntegerField(
        default=0, validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user} - {self.technology.name} - {self.progress_percentage}%"

    def calculate_progress(self):

        modules = self.technology.modules.all()
        topics = Topic.objects.filter(module__in=modules)
        total_questions = Question.objects.filter(topic__in=topics).count()
        good_knowledge_count = UserQuestionKnowledge.objects.filter(
            user=self.user, question__topic__in=topics, knowledge_status="good"
        ).count()

        if total_questions > 0:
            self.progress_percentage = (good_knowledge_count / total_questions) * 100
        else:
            self.progress_percentage = 0

        self.save()
