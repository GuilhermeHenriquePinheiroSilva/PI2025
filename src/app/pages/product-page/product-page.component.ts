import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router, RouterModule } from '@angular/router';
import { Title } from '@angular/platform-browser';

import { NavBarComponent } from '../shared/nav-bar/nav-bar.component';
import { FooterComponent } from '../shared/footer/footer.component';

import { GiftCard, GiftcardService } from '../../../services/giftcard.service';
import { NotificationService } from '../../../services/notification.service';
import { CartService } from '../../../services/cart.service';
import { AuthService } from '../../../services/auth.service';
import { User } from '../../models/user.model';

@Component({
  selector: 'app-product-page',
  standalone: true,
  imports: [
    CommonModule,
    RouterModule,
    NavBarComponent,
    FooterComponent
  ],
  templateUrl: './product-page.component.html',
  styleUrls: ['./product-page.component.css']
})
export class ProductPageComponent implements OnInit {
  quantidade: number = 1;
  giftCard: GiftCard | null = null;
  isLoading: boolean = true;
  user: User | null = null;

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private giftcardService: GiftcardService,
    private notificationService: NotificationService,
    private cartService: CartService,
    private authService: AuthService,
    private titleService: Title
  ) {}

  ngOnInit(): void {
    this.titleService.setTitle("GoGift | Detalhes do Produto");
    this.quantidade = 1;
    this.carregarDetalhesDoGiftCard();

    this.authService.user$.subscribe(user => {
      this.user = user;
    });
  }

  carregarDetalhesDoGiftCard(): void {
    const id = this.route.snapshot.paramMap.get('id');
    if (id) {
      this.isLoading = true;
      this.giftcardService.getGiftCardById(id).subscribe({
        next: (data) => {
          this.giftCard = data;
          this.isLoading = false;
        },
        error: (err) => {
          console.error('Erro ao buscar detalhes do gift card:', err);
          this.notificationService.show('Erro ao carregar o produto.', 'error');
          this.isLoading = false;
        }
      });
    } else {
      console.error('ID do Gift Card não encontrado na rota.');
      this.isLoading = false;
    }
  }

  // CORREÇÃO: Renomeando o método para corresponder ao HTML
  incrementarQuantidade(): void {
    if (this.giftCard && this.quantidade < this.giftCard.quantityavailable) {
      this.quantidade++;
    } else {
      this.notificationService.show('Quantidade máxima em estoque atingida.', 'warning');
    }
  }

  // CORREÇÃO: Renomeando o método para corresponder ao HTML
  decrementarQuantidade(): void {
    if (this.quantidade > 1) {
      this.quantidade--;
    }
  }

  adicionarAoCarrinho(): void {
    if (!this.user) {
      this.notificationService.show('Você precisa estar logado para adicionar itens ao carrinho.', 'warning');
      this.router.navigate(['/login']);
      return;
    }

    if (this.giftCard) {
      this.cartService.addToCart(this.giftCard, this.quantidade);
    }
  }

  comprarAgora(): void {
    if (!this.user) {
      this.notificationService.show('Você precisa estar logado para comprar.', 'warning');
      this.router.navigate(['/login']);
      return;
    }

    if (this.giftCard) {
       this.cartService.addToCart(this.giftCard, this.quantidade);
       this.router.navigate(['/cart']);
    }
  }
}