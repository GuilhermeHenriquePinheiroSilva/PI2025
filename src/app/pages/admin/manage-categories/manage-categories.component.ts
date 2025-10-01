// Em Front/src/app/pages/admin/manage-categories/manage-categories.component.ts

import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { Category, CategoryService } from '../../../../services/category.service';
import { NotificationService } from '../../../../services/notification.service';


@Component({
  selector: 'app-manage-categories',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './manage-categories.component.html',
  styleUrls: ['./manage-categories.component.css']
})
export class ManageCategoriesComponent implements OnInit {
  categories: Category[] = [];
  categoryForm: FormGroup;
  isEditMode = false;
  currentCategoryId: number | null = null;
  isLoading = false;

  constructor(
    private categoryService: CategoryService,
    private fb: FormBuilder,
    private notificationService: NotificationService
  ) {
    this.categoryForm = this.fb.group({
      name: ['', Validators.required]
    });
  }

  ngOnInit(): void {
    this.loadCategories();
  }

  loadCategories(): void {
    this.isLoading = true; // <-- ADICIONE ESTA LINHA
    this.categoryService.getCategories().subscribe(data => {
      this.categories = data;
      this.isLoading = false; // <-- ADICIONE ESTA LINHA
    });
  }

  onSubmit(): void {
  if (this.categoryForm.invalid) {
    return;
  }

  this.isLoading = true;
  const categoryName = this.categoryForm.value.name;

  if (this.isEditMode && this.currentCategoryId !== null) {
    // --- MODO DE EDIÇÃO ---
    this.categoryService.updateCategory(this.currentCategoryId, categoryName).subscribe({
      // Função para sucesso
      next: () => {
        this.notificationService.show('Categoria atualizada com sucesso!', 'success');
        this.resetForm();
        this.loadCategories();
      },
      // Função para erro (SINTAXE CORRIGIDA)
      error: () => {
        this.notificationService.show('Erro ao atualizar categoria.', 'error');
        this.isLoading = false;
      }
    });
  } else {
    // --- MODO DE CRIAÇÃO ---
    this.categoryService.createCategory(categoryName).subscribe({
      // Função para sucesso
      next: () => {
        this.notificationService.show('Categoria criada com sucesso!', 'success');
        this.resetForm();
        this.loadCategories();
      },
      // Função para erro (SINTAXE CORRIGIDA)
      error: () => {
        this.notificationService.show('Erro ao criar categoria.', 'error');
        this.isLoading = false;
      }
    });
  }
}

  editCategory(category: Category): void {
    this.isEditMode = true;
    this.currentCategoryId = category.id;
    this.categoryForm.setValue({ name: category.name });
  }

  deleteCategory(id: number): void {
    if (confirm('Tem certeza que deseja deletar esta categoria?')) {
      this.categoryService.deleteCategory(id).subscribe({
        next: () => {
          this.notificationService.show('Categoria deletada com sucesso!', 'success');
          this.loadCategories();
        },
        error: () => this.notificationService.show('Erro ao deletar categoria.', 'error')
      });
    }
  }

  resetForm(): void {
    this.isEditMode = false;
    this.currentCategoryId = null;
    this.categoryForm.reset();
  }
}