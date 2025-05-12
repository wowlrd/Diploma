from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import PromptData, QuizQuestion, Grade
# from .forms import ProfileImageForm
from django.db.models import Avg, Max, Count
from .helper import find_similarity, chatGPT, image
from django.http import JsonResponse
import json
import random
import time
import io
import matplotlib
import matplotlib.pyplot as plt
from io import BytesIO
import base64

matplotlib.use('Agg')

@login_required(login_url='login')
def home(request):
    db_obj = PromptData.objects.filter(userid=request.user)

    if request.method == 'POST':
        if 'clear_history' in request.POST:
            PromptData.objects.filter(userid=request.user).delete()
            for key in ('quiz_score','quiz_total','quiz_start_global','used_question_ids','quiz_subject'):
                request.session.pop(key, None)
            return redirect('home')

        elif 'subject' in request.POST and 'prompt' not in request.POST:
            request.session['quiz_subject'] = request.POST['subject']
            messages.success(request, f"Subject set to {request.POST['subject']}")
            return redirect('home')

        elif 'prompt' in request.POST:
            prompt = request.POST.get('prompt','').strip().lower()

            if prompt.lower() == 'quiz':
                
                request.session['quiz_start_global'] = time.time()
                request.session['quiz_score'] = 0
                request.session['quiz_total'] = 1
                request.session['used_question_ids'] = []

              
                subject = request.session.get('quiz_subject', 'all')
               
                if subject == 'all':
                    qs = QuizQuestion.objects.all()
                else:
                    qs = QuizQuestion.objects.filter(subject__iexact=subject)

                question = qs.order_by('?').first()
                if question:
                    request.session['quiz_question_id'] = question.id
                    request.session['quiz_start_time'] = time.time()
                    request.session['used_question_ids'] = [question.id]

                    PromptData.objects.create(
                        userid=request.user,
                        prompt="Start quiz",
                        output=(
                            f"Subject: {question.subject}\n\n"
                            f"Question 1/5:\n{question.question}\n\n"
                            f"A. {question.option_a}\n"
                            f"B. {question.option_b}\n"
                            f"C. {question.option_c}\n"
                            f"D. {question.option_d}"
                        )
                    )
                return redirect('home')

            elif prompt.strip().upper() in ['A', 'B', 'C', 'D']:
                question_id = request.session.get('quiz_question_id')
                start_time = request.session.get('quiz_start_time')
                if question_id:
                    try:
                        question = QuizQuestion.objects.get(id=question_id)
                        correct = question.correct_option.upper()
                        score = request.session.get('quiz_score', 0)
                        total = request.session.get('quiz_total', 0)
                        elapsed_time = int(time.time() - start_time) if start_time else None

                        if prompt.upper() == correct:
                            result = "Correct!"
                            request.session['quiz_score'] = score + 1
                            score += 1
                        else:
                            explanation = question.explanation or "No explanation provided."
                            result = f"Wrong! Correct answer: {correct}\n\nExplanation: {explanation}"

                        if elapsed_time is not None:
                            minutes = elapsed_time // 60
                            seconds = elapsed_time % 60
                            time_display = f"{minutes} min {seconds} sec" if minutes else f"{seconds} sec"
                            result += f" (Answered in {time_display})"

                        PromptData.objects.create(userid=request.user, prompt=prompt, output=result)
                        del request.session['quiz_question_id']
                        request.session.pop('quiz_start_time', None)

                        if total >= 5:
                            quiz_start_global = request.session.get('quiz_start_global')
                            if not quiz_start_global:
                                quiz_start_global = time.time() - 1
                            total_seconds = int(time.time() - quiz_start_global)
                            minutes = total_seconds // 60
                            seconds = total_seconds % 60
                            time_display = f"{minutes} min {seconds} sec" if minutes else f"{seconds} sec"
                            grade = round((score / total) * 100)

                            if grade >= 90:
                                feedback = "Excellent work! You nailed it 💪"
                            elif grade >= 70:
                                feedback = "Good job! A little more practice and you'll master it!"
                            else:
                                feedback = "Don't give up! Mistakes help you learn ✨"

                            final_msg = (
                                f"Quiz completed! Final Score: {score}/{total} ({grade}%)\n"
                                f"Total time: {time_display}\n{feedback}"
                            )
                            PromptData.objects.create(userid=request.user, prompt="Quiz Summary", output=final_msg)
                            Grade.objects.create(user=request.user, score=score, total=total, percentage=grade)

                            request.session.pop('quiz_score', None)
                            request.session.pop('quiz_total', None)
                            request.session.pop('quiz_start_global', None)
                            request.session.pop('used_question_ids', None)
                            request.session.pop('quiz_subject', None)

                        else:
                            used_questions = request.session.get('used_question_ids', [])
                            quiz_subject = request.session.get('quiz_subject', 'all')
                            question_set = QuizQuestion.objects.exclude(id__in=used_questions)
                            if quiz_subject != 'all':
                                question_set = question_set.filter(subject__iexact=quiz_subject)
                            next_question = question_set.order_by('?').first()
                            if next_question:
                                used_questions.append(next_question.id)
                                request.session['used_question_ids'] = used_questions
                                request.session['quiz_question_id'] = next_question.id
                                request.session['quiz_start_time'] = time.time()
                                request.session['quiz_total'] = total + 1

                                PromptData.objects.create(
                                    userid=request.user,
                                    prompt="Next question",
                                    output=(
                                        f"Question {total + 1}/5:\n"
                                        f"{next_question.question}\n"
                                        f"\nA. {next_question.option_a}\n"
                                        f"B. {next_question.option_b}\n"
                                        f"C. {next_question.option_c}\n"
                                        f"D. {next_question.option_d}"
                                    )
                                            )
                    except QuizQuestion.DoesNotExist:
                     pass
                return redirect('home')


            elif 'quiz_question_id' in request.session:
                PromptData.objects.create(
                    userid=request.user,
                    prompt=prompt,
                    output="Please enter the answer as A, B, C, or D."
                )
                return redirect('home')

            elif prompt.lower() == 'score':
                total = request.session.get('quiz_total', 0)
                score = request.session.get('quiz_score', 0)
                output = f"Your current score is {score}/{total}."
                PromptData.objects.create(userid=request.user, prompt=prompt, output=output)
                return redirect('home')

            response = find_similarity(prompt)
            try:
                    link = image(prompt)
            except:
                    link = ""

            if response == []:
                    response = chatGPT(prompt)
            else:
                    response = response[0][1]

            PromptData.objects.create(
                userid=request.user, prompt=prompt, output=response, img=link
            )

        return redirect('home')

    data_list   = list(db_obj.values("prompt","output"))
    data_json   = json.dumps(data_list, ensure_ascii=False)
    subjects    = QuizQuestion.objects.values_list('subject', flat=True).distinct()

    quiz_subject = request.session.get('quiz_subject','all')

    return render(request, 'base.html', {
        'data':        db_obj,
        'data_json':   data_json,
        'subjects':    subjects,
        'quiz_subject': quiz_subject, 
        'subjects': QuizQuestion.objects.values_list('subject', flat=True).distinct(),
        'quiz_active': True,
        'grades_active': False,
    })

@login_required
def grades_view(request):
    grades = Grade.objects.filter(user=request.user).order_by('created_at')
    context = {'grades': grades}

    chart = None
    if grades.exists():
        labels = [f"Quiz {i+1}" for i in range(len(grades))]
        scores = [grade.percentage for grade in grades]
        plt.figure(figsize=(10, 5))
        plt.plot(labels, scores, marker='o', linestyle='-', color='#7B4AE2', linewidth=3.5)
        plt.fill_between(labels, scores, alpha=0.15, color='#c6a8ff')
        plt.xlabel("Quiz Attempts", fontsize=14, color='#3D155F')
        plt.ylabel("Score (%)", fontsize=14, color='#3D155F')

        plt.ylim(0, 110)
        plt.grid(True, linestyle='--', alpha=0.3)
        plt.xticks(rotation=45, fontsize=12, color='#3D155F')
        plt.yticks(fontsize=12, color='#3D155F')
        plt.tight_layout()

        min_score = min(scores)
        max_score = max(scores)
        y_min = max(0, min_score - 10) if min_score > 0 else -5
        y_max = min(100, max_score + 10) if max_score < 100 else 105
        plt.ylim(y_min, y_max)

        buffer = io.BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        chart = base64.b64encode(buffer.read()).decode('utf-8')
        buffer.close()
        plt.close()

        plt.close()

    return render(request, 'grades.html', {'grades': grades, 'chart': chart})

@login_required(login_url='login')
def clear_history(request):
    PromptData.objects.filter(userid=request.user).delete()
    request.session.pop('quiz_score', None)
    request.session.pop('quiz_total', None)
    return redirect('home')

def login_user(request):
    if request.user.is_authenticated:
        return redirect('main')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('main')
        else:
            messages.error(request, 'Invalid credentials')

    return render(request, 'login.html')

def register_user(request):
    if request.user.is_authenticated:
        return redirect('main')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()

        if not username or not password:
            messages.error(request, 'Введите имя пользователя и пароль.')
        elif User.objects.filter(username=username).exists():
            messages.error(request, 'Пользователь с таким именем уже существует.')
        else:
            try:
                user = User.objects.create_user(username=username, password=password)
                login(request, user)
                PromptData.objects.create(userid=user)
                return redirect('main')
            except Exception as e:
                messages.error(request, f'Ошибка при регистрации: {e}')

    return render(request, 'register.html')

def logout_user(request):
    logout(request)
    return redirect('login')

@login_required(login_url='login')
def main_page(request):
    return render(request, 'main.html')

@login_required(login_url='login')
def chat_interface(request):
    db_obj = PromptData.objects.filter(userid=request.user)
    return render(request, 'home.html', {'data': db_obj})

@login_required
def user(request):
    return render(request, 'user.html')

@login_required(login_url='login')
def about(request):
    return render(request, 'about.html')

@login_required(login_url='login')
def user(request):
    from .models import Grade

    stats = Grade.objects.filter(user=request.user) \
        .aggregate(
            total=Count('id'),
            average=Avg('percentage'),
            best=Max('percentage')
        )
    context = {
        'user': request.user,
        'total_quizzes': stats['total'] or 0,
        'average_score': round(stats['average'] or 0, 1),
        'best_score': stats['best'] or 0,
    }
    return render(request, 'user.html', context)

# @login_required
# def change_picture(request):
#     profile, created = Profile.objects.get_or_create(user=request.user)
#     if request.method == 'POST':
#         form = ProfileImageForm(request.POST, request.FILES, instance=profile)
#         if form.is_valid():
#             form.save()
#             return redirect('user')  # or wherever you show the profile
#     else:
#         form = ProfileImageForm(instance=profile)
#     return render(request, 'chatbot/change_picture.html', {
#         'form': form,
#         'profile': profile
#     })

# @login_required
# def upload_profile_picture(request):
#     if request.method == 'POST' and request.FILES.get('profile_picture'):
#         profile = request.user.profile  # adjust if you store it elsewhere
#         profile.picture = request.FILES['profile_picture']
#         profile.save()
#         return JsonResponse({
#             'status': 'ok',
#             'url': profile.picture.url
#         })
#     return JsonResponse({'status': 'error'}, status=400)