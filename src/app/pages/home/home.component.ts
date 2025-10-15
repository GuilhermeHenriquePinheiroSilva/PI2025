import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { GiftcardService, GiftCard } from '../../../services/giftcard.service';
import { GiftCardTemplateComponent } from '../shared/gift-card-template/gift-card-template.component';
import { NavBarComponent } from '../shared/nav-bar/nav-bar.component';
import { FooterComponent } from '../shared/footer/footer.component';
import { Category } from '../../models/category.model';
import { CategoryService } from '../../../services/category.service';

@Component({
  selector: 'app-home',
  standalone: true,
  imports: [
    CommonModule,
    RouterLink,
    NavBarComponent,
    FooterComponent,
    GiftCardTemplateComponent
  ],
  templateUrl: './home.component.html',
  styleUrl: './home.component.css'
})
export class HomeComponent implements OnInit {
  // Lista para a seção "Mais Vendidos"
  maisVendidos: GiftCard[] = [];
  // Lista para a seção "Mais Amados"
  maisAmados: GiftCard[] = [];

  randomCategories: Category[] = [];

  isLoading: boolean = true;

  private categoryColors: string[] = ['#E68210', '#C9720E', '#5B4B3F', '#705C4E', '#1D1302'];


  constructor(private giftcardService: GiftcardService, private categoryService: CategoryService) { }

  ngOnInit(): void {
    this.carregarCardsDaHome();
    this.loadRandomCategories();
  }

  carregarCardsDaHome(): void {
    this.isLoading = true;

    // Busca todos os cards para a seção "Mais Vendidos"
    this.giftcardService.getAllGiftCards().subscribe({
      next: (data) => {
        this.maisVendidos = data;
      },
      error: (err) => {
        console.error('Erro ao carregar os gift cards:', err);
      }
    });

    // Busca os cards com maior nota para a seção "Mais Amados"
    this.giftcardService.getTopRatedGiftCards().subscribe({
      next: (data) => {
        this.maisAmados = data;
        this.isLoading = false; // Considera o carregamento completo após a segunda chamada
      },
      error: (err) => {
        console.error('Erro ao carregar os gift cards mais amados:', err);
        this.isLoading = false;
      }
    });
  }

  loadRandomCategories(): void {
    this.categoryService.getCategories().subscribe({
      next: (allCategories) => {
        for (let i = allCategories.length - 1; i > 0; i--) {
          const j = Math.floor(Math.random() * (i + 1));
          [allCategories[i], allCategories[j]] = [allCategories[j], allCategories[i]];
        }
        this.randomCategories = allCategories.slice(0, 5);
        this.isLoading = false;
      },
      error: (err) => {
        console.error('Erro ao carregar categorias:', err);
        this.isLoading = false;
      }
    });
  }

  // Função para obter a cor da categoria de forma cíclica
  getCategoryColor(index: number): string {
    return this.categoryColors[index % this.categoryColors.length];
  }
}
