from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('hot/', views.hot, name='hot'),
    path('question/<int:question_id>/', views.question, name='question'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('signup/', views.signup, name='signup'),
    path('profile/edit/', views.settings_profile, name='profile_edit'),
    path('ask/', views.ask, name='ask'),
    path('tag/<str:tag_name>/', views.tag, name='tag'),
    path('question/like/', views.question_like, name='question_like'),
    path('answer/like/', views.answer_like, name='answer_like'),
    path('answer/mark-correct/', views.mark_correct_answer, name='mark_correct_answer'),
    path('search/', views.search_suggestions, name='search_suggestions')
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
