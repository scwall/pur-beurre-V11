from django.contrib import messages
from django.contrib.auth import authenticate, login, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.shortcuts import render, redirect
from django.urls import reverse

from food_and_search.models import Categorie, Product, SignUpForm


# View for index.html
def index(request):
    return render(request, 'index.html')


# View for save_product.html login required for show save product
@login_required(login_url='/login/')
def save_product(request):
    current_user = request.user
    user_products = Product.objects.filter(user_product__exact=current_user.id).order_by('pk')
    paginator = Paginator(user_products, 6)
    if request.method == 'GET':
        page = request.GET.get('page')
        products_paginator = paginator.get_page(number=page)
        context = {'products': products_paginator}
        if not products_paginator.has_next() and paginator.count % 6 != 0:
            context['row'] = True
        return render(request, 'save_product.html', context)
    if request.method == 'POST':
        current_user = request.user
        page = request.POST.get('page')
        if page is '':
            page = 0
        id_product = request.POST.get('product_form')
        product = Product.objects.get(id=id_product)
        product.user_product.remove(current_user)
        return redirect(
            reverse(
                'food_and_search:save_product') + '?page={page}'.format(page=page))


# View for result product, using paginator for show products in many page
def result(request):
    if request.method == 'GET':
        name_product_search = request.GET.get('product')
        save_product = request.GET.get('product-save')
        if save_product is not None:
            save_product = int(save_product)
        if name_product_search is None:
            raise Http404('Aucun produit demandé !')
        else:
            product = Product.objects.filter(name__icontains=name_product_search)

            if product.exists():
                original_product = product[0]
                categories = Categorie.objects.filter(products__id=product[0].id)
                if request.GET.get('category_selected') is not None:
                    category = request.GET.get('category_selected')
                    products = Product.objects.filter(categorie__id=category).order_by('nutrition_grade')
                else:
                    products = Product.objects.filter(categorie__in=categories).order_by('nutrition_grade')
                paginator = Paginator(products, 6)
                page = request.GET.get('page')
                products_paginator = paginator.get_page(number=page)
                context = {'products': products_paginator, 'name_product_search': name_product_search,
                           'original_product': original_product, 'id_product': save_product,
                           'categories': categories}

            else:
                raise Http404(
                    "le produit {product} n'existe pas dans la base de données".format(product=name_product_search))
        return render(request, 'result_product.html', context)
    if request.method == 'POST':
        context = {}
        if request.user.is_authenticated:
            current_user = request.user
            id_product = request.POST.get('product_form')
            name_product_search = request.POST['name_product_search']
            page = request.POST.get('page')
            product = Product.objects.get(id=id_product)
            product.user_product.add(current_user)
            context['id_product'] = int(id_product)
        else:
            return redirect('/login')

        return redirect(
            reverse(
                'food_and_search:result') + '?product={name_product}&product-save={product_save}&page={page}'.format(
                product_save=id_product, name_product=name_product_search, page=page))


# View detail product
def detail_product(request, pk):
    product = get_object_or_404(Product, pk=pk)
    return render(request, template_name='detail_product.html', context={'detail_product': product})


# Views user
@login_required(login_url='/login/')
def user_account(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important!
            messages.success(request, "Votre mot de passe a été mis à jour avec succès!")
        else:
            messages.error(request, "Veuillez corriger l'erreur ci-dessous")
    else:
        form = PasswordChangeForm(request.user)
    return render(request,'user_page.html',{'form':form})


# Form and view for user registration
def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()

            tmp_username = form.cleaned_data.get('username')
            tmp_password = form.cleaned_data.get('password1')
            user = authenticate(username=tmp_username, password=tmp_password)
            login(request, user)
            return redirect('/')
    else:
        form = SignUpForm()
    return render(request, 'signup.html', {'form': form})
