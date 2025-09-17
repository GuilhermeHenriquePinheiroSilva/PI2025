import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { switchMap } from 'rxjs/operators';

import { GiftcardService, GiftCard } from '../../../services/giftcard.service';
import { GiftCardTemplateComponent } from '../shared/gift-card-template/gift-card-template.component';
import { NavBarComponent } from '../shared/nav-bar/nav-bar.component';
import { FooterComponent } from '../shared/footer/footer.component';

@Component({
  selector: 'app-search',
  standalone: true,
  imports: [
    CommonModule,
    RouterLink,
    NavBarComponent,
    FooterComponent,
    GiftCardTemplateComponent
  ],
  templateUrl: './search.component.html',
  styleUrl: './search.component.css'
})
export class SearchComponent implements OnInit {
  giftCards: GiftCard[] = [];
  searchTerm: string | null = null;
  isLoading: boolean = true;

  constructor(
    private giftcardService: GiftcardService,
    private route: ActivatedRoute // Injeta o serviço de rota para ler a URL
  ) {}

  ngOnInit(): void {
    // Ouve as mudanças nos parâmetros da URL (ex: ?q=...)
    this.route.queryParamMap.pipe(
      switchMap(params => {
        this.isLoading = true;
        this.searchTerm = params.get('q'); // Pega o valor do parâmetro 'q' da URL
        
        if (this.searchTerm) {
          // Se houver um termo de busca, chama o serviço de busca
          return this.giftcardService.searchGiftCards(this.searchTerm);
        } else {
          // Se não houver, busca todos os gift cards
          return this.giftcardService.getAllGiftCards();
        }
      })
    ).subscribe({
      next: (data) => {
        this.giftCards = data;
        this.isLoading = false;
        console.log('Dados recebidos:', data);
      },
      error: (err) => {
        console.error('Erro ao buscar gift cards:', err);
        this.isLoading = false;
      }
    });
  }
}
