import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { GiftcardService, GiftCard } from '../../../services/giftcard.service';
import { GiftCardTemplateComponent } from '../shared/gift-card-template/gift-card-template.component';
import { NavBarComponent } from '../shared/nav-bar/nav-bar.component';
import { FooterComponent } from '../shared/footer/footer.component';

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
  // Nova lista para a seção "Mais Amados"
    maisAmados: GiftCard[] = [];

  isLoading: boolean = true;

  constructor(private giftcardService: GiftcardService) { }

  ngOnInit(): void {
    this.carregarCardsDaHome();
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
}
