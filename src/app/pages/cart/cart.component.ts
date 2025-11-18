// src/app/pages/cart/cart.component.ts
import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterModule } from '@angular/router';

import { NavBarComponent } from '../shared/nav-bar/nav-bar.component';
import { CartService, CartItem } from '../../../services/cart.service';
import { PurchaseService } from '../../../services/purchase.service';
import { NotificationService } from '../../../services/notification.service';
import { EmptyCartComponent } from '../empty-cart/empty-cart.component';

@Component({
  selector: 'app-cart',
  standalone: true,
  imports: [
    CommonModule,
    RouterModule,
    NavBarComponent,
    EmptyCartComponent
  ],
  templateUrl: './cart.component.html',
  styleUrls: ['./cart.component.css']
})
export class CartComponent implements OnInit {
  cartItems: CartItem[] = [];
  
  // Variáveis para o resumo financeiro detalhado
  totalProdutosBase: number = 0;   // Soma dos 'desired_amount'
  taxaPlataforma: number = 0;      // Soma das taxas de 3% (valor - desired_amount)
  subtotalComPlataforma: number = 0; // Soma dos 'valor' (Base + Plataforma)
  taxaServico: number = 0;         // 5% sobre o subtotalComPlataforma
  totalPedido: number = 0;         // Valor final a pagar

  isLoading = false;

  constructor(
    private cartService: CartService,
    private purchaseService: PurchaseService,
    private notificationService: NotificationService,
    private router: Router
  ) {}

  ngOnInit(): void {
    this.cartService.cart$.subscribe(items => {
      this.cartItems = items;
      this.calcularTotais();
    });
  }

  increaseQuantity(item: CartItem): void {
    this.cartService.updateQuantity(item.product.id, item.quantity + 1);
  }

  decreaseQuantity(item: CartItem): void {
    this.cartService.updateQuantity(item.product.id, item.quantity - 1);
  }

  removeItem(item: CartItem): void {
    this.cartService.removeItem(item.product.id);
  }

  calcularTotais(): void {
    this.totalProdutosBase = 0;
    this.taxaPlataforma = 0;
    this.subtotalComPlataforma = 0;

    this.cartItems.forEach(item => {
      const qtd = item.quantity;
      const valorVenda = Number(item.product.valor);
      const valorDesejado = Number(item.product.desired_amount);

      // 1. Valor base (o que o vendedor quer receber)
      this.totalProdutosBase += valorDesejado * qtd;

      // 2. Taxa da Plataforma (diferença entre venda e desejado)
      // Se por acaso valorVenda for menor que desejado (erro), assumimos 0 taxa
      const taxaItem = Math.max(0, valorVenda - valorDesejado);
      this.taxaPlataforma += taxaItem * qtd;
      
      // 3. Subtotal (Preço de venda dos itens)
      this.subtotalComPlataforma += valorVenda * qtd;
    });

    // 4. Taxa de Serviço (5% sobre o valor de venda dos itens)
    this.taxaServico = this.subtotalComPlataforma * 0.05;

    // 5. Total Final
    this.totalPedido = this.subtotalComPlataforma + this.taxaServico;
  }

  finalizarCompra(): void {
    if (this.cartItems.length === 0) {
      this.notificationService.show('Seu carrinho está vazio!', 'warning');
      return;
    }

    this.isLoading = true;
    this.notificationService.show('Redirecionando para o pagamento...', 'info');

    this.purchaseService.createCartPreference(this.cartItems).subscribe({
      next: (response) => {
        if (response && response.init_point) {
          window.location.href = response.init_point;
        } else {
          this.notificationService.show('Não foi possível iniciar o pagamento. Tente novamente.', 'error');
          this.isLoading = false;
        }
      },
      error: (err) => {
        const errorMessage = err.error?.detail || 'Ocorreu um erro desconhecido.';
        this.notificationService.show(`Erro: ${errorMessage}`, 'error');
        this.isLoading = false;
      }
    });
  }
}