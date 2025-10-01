// front/src/app/pages/category-page/category-page.component.ts
import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { GiftCard, GiftcardService } from '../../../services/giftcard.service';

import { Category } from '../../models/category.model';
import { CategoryService } from '../../../services/category.service';
import { GiftCardTemplateComponent } from '../shared/gift-card-template/gift-card-template.component';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-category-page',
  standalone: true,
  imports: [CommonModule, RouterLink,GiftCardTemplateComponent],
  templateUrl: './category-page.component.html',
  styleUrls: ['./category-page.component.css'],
})
export class CategoryPageComponent implements OnInit {
  giftCards: GiftCard[] = [];
  category: Category | undefined;
  isLoading = true;

  constructor(
    private route: ActivatedRoute,
    private giftcardService: GiftcardService,
    private categoryService: CategoryService
  ) { }

  ngOnInit(): void {
    this.route.paramMap.subscribe(params => {
      const categoryId = Number(params.get('id'));
      if (categoryId) {
        this.loadGiftCards(categoryId);
        this.loadCategoryDetails(categoryId);
      }
    });
  }

  loadGiftCards(categoryId: number): void {
    this.isLoading = true;
    this.giftcardService.getGiftCardsByCategory(categoryId).subscribe(
      (data) => {
        this.giftCards = data;
        this.isLoading = false;
      },
      (error) => {
        console.error('Erro ao buscar gift cards por categoria', error);
        this.isLoading = false;
      }
    );
  }

  loadCategoryDetails(categoryId: number): void {
    // Supondo que você tenha um método no seu service para buscar uma categoria pelo ID
    // Se não tiver, pode buscar todas e filtrar, ou criar o endpoint no backend.
    this.categoryService.getCategories().subscribe(categories => {
      this.category = categories.find(c => c.id === categoryId);
    });
  }
}