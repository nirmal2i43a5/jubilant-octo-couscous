from django.core.exceptions import ValidationError
from django.shortcuts import render,redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib import messages
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic import DetailView,ListView
from django.forms import widgets
from django.forms import inlineformset_factory
from django.db import transaction
from django.urls import reverse_lazy
from Inventory.models import *
from .models import Sales, SalesItem
from .forms import *
@login_required
def sales_list(request):
    sales=Sales.objects.all().order_by('-id')
    return render(request,'sales/sales_list.html',{'sales':sales})

class SalesCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView, ListView):
    model = Sales
    template_name = "sales/sales_form.html"
    fields = '__all__'
    success_message = "New sales successfully added."

    def get_context_data(self, **kwargs):
        self.object_list=self.get_queryset()
        data = super(SalesCreateView, self).get_context_data(**kwargs)
        if self.request.POST:
            data['items'] = SaleItemFormset(self.request.POST)
        else:
            data['items'] = SaleItemFormset()
            data['product'] = Product.objects.all()

        return data

    def form_valid(self, form):
        context = self.get_context_data()
        items = context['items']
        with transaction.atomic():
            if items.is_valid():
                items.instance = form.save(commit=False)
                for i in items:
                    prod = i.cleaned_data['product']
                    product=prod.product
                    qt=i.cleaned_data['quantity']
                    sold_item=Product.objects.get(product=product)
                    if sold_item.Quantity < qt:
                        form.errors['value']='Your entered quantity exceeds inventory quantity'
                        return self.form_invalid(form)
                    else:
                        sold_item.Quantity -=qt
                        sold_item.save()
                        form.save()
                        items.save()
        return super(SalesCreateView, self).form_valid(form)

    def get_initial(self):
        initial=super(SalesCreateView,self).get_initial()
        initial['customer']=Customer.objects.get(pk=self.kwargs['pk'])
        return initial

class CustomerAddView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = Customer
    template_name = "sales/add_customer.html"
    fields = '__all__'
    success_message = "New Customer successfully added."


class SalesDetail(LoginRequiredMixin,DetailView):
    model = Sales
    template_name = 'sales/sales_detail.html'

    def get_context_data(self, **kwargs):
        context = super(SalesDetail, self).get_context_data(**kwargs)
        return context

def SalesUpdateView(request, sales_id):
    sale = Sales.objects.get(id=sales_id)
    form = SaleForm(request.POST, instance=sale)
    ItemFormset = inlineformset_factory(Sales, SalesItem, form=SaleForm, extra=0)

    if request.method == 'POST':
        formset = ItemFormset(request.POST, instance=sale)

        if formset.is_valid():
            form.save()
            formset.save()
            from django.contrib import messages
            messages.success(request, 'Order successfully updated')
    else:

        form = SaleForm(instance=sale)
        formset = ItemFormset(instance=sale)

    return render(request, 'sales/sales_update.html', {'form':form, 'formset' : formset})


def sales_return_list(request):
    sales=Sales.objects.all().order_by('-id')
    return render(request,'sales/sales_return_list.html',{'sales':sales})

def existing_customer_list(request):
    sales=Customer.objects.all()
    return render(request,'sales/existing_customer.html',{'sales':sales})


class existing_sales_create(LoginRequiredMixin, SuccessMessageMixin, CreateView, ListView):
    model = Sales
    template_name = "sales/sales_form.html"
    fields = '__all__'
    success_message = "New sales successfully added."

    def get_context_data(self, **kwargs):
        self.object_list=self.get_queryset()

        data = super(existing_sales_create, self).get_context_data(**kwargs)
        if self.request.POST:
            data['items'] = SaleItemFormset(self.request.POST)
        else:
            data['items'] = SaleItemFormset()
            data['product'] = Product.objects.all()
        return data
    # def get_queryset(self):
    #     data=self.get_context_data()

    def form_valid(self, form):
        context = self.get_context_data()
        items = context['items']
        with transaction.atomic():
            if items.is_valid():
                items.instance = form.save(commit=False)
                for i in items:
                    prod = i.cleaned_data['product']
                    product=prod.product
                    qt=i.cleaned_data['quantity']
                    sold_item=Product.objects.get(product=product)
                    if sold_item.Quantity > qt:
                        sold_item.Quantity -= qt
                        sold_item.save()
                        form.save()
                        items.save()
                    else:
                        form.errors['value'] = 'Your entered quantity exceeds inventory quantity'
                        return self.form_invalid(form)
        return super(existing_sales_create, self).form_valid(form)

    def get_initial(self):
        initial = super(existing_sales_create, self).get_initial()
        initial['customer'] = Customer.objects.get(pk=self.kwargs['pk'])
        return initial

class SalesReturnView(LoginRequiredMixin,DetailView,UpdateView):
    model = Sales
    fields='__all__'
    template_name = 'sales/sales_return_update.html'

    def get_context_data(self, **kwargs):
        data = super(SalesReturnView, self).get_context_data(**kwargs)
        if self.request.POST:
            data['items'] = SaleItemFormset(self.request.POST)
        else:
            data['items'] = SaleItemFormset()
        return data

    def form_valid(self, form):
        context = self.get_context_data()
        print(context)
        name=context['object']
        name_id=Customer.objects.get(name=name)
        sales_id=Sales.objects.get(customer_id=name_id)
        items = context['items']
        with transaction.atomic():
            if items.is_valid():
                items.instance = form.save(commit=False)
                for i in items:
                    prod = i.cleaned_data['product']
                    qt=i.cleaned_data['quantity']
                    product=prod.product
                    sales_item_id = SalesItem.objects.filter(sales_id_id=sales_id, product_id=prod.id)
                    for i in sales_item_id:
                        i.quantity -= qt
                        i.save()
                        sold_item=Product.objects.get(product=product)
                        sold_item.Quantity +=qt
                        sold_item.save()
        return super(SalesReturnView, self).form_valid(form)



def load_products(request,pk):
    prod = SalesItem.objects.filter(sales_id=pk).all()
    return render(request, 'sales/product_dropdown_list_options.html',  {'prod': prod})

class sales_return_view(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = salesReturn
    template_name = "sales/sales_return1.html"
    fields = '__all__'
    success_message = "New sales successfully added."
    context_object_name='yogsh'

    def get_initial(self):
        initial=super(sales_return_view,self).get_initial()
        initial['sales_return_id']=Customer.objects.get(pk=self.kwargs['pk'])
        return initial
