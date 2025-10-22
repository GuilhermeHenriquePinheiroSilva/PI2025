// src/app/pages/add-gc/add-gc.component.ts

import { Component, OnInit, computed, effect, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
// ... outras importações ...
import { ImageCroppedEvent, ImageCropperComponent, LoadedImage } from 'ngx-image-cropper';
import { NavBarComponent } from '../shared/nav-bar/nav-bar.component';
import { FooterComponent } from '../shared/footer/footer.component';
import { GiftcardService } from '../../../services/giftcard.service';
import { NotificationService } from '../../../services/notification.service';
import { Category } from '../../models/category.model';
import { CategoryService } from '../../../services/category.service';

@Component({
  selector: 'app-add-gc',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    RouterLink,
    NavBarComponent,
    FooterComponent,
    ImageCropperComponent // Importe aqui
  ],
  templateUrl: './add-gc.component.html',
  styleUrls: ['./add-gc.component.css']
})
export class AddGcComponent implements OnInit {
  titulo: string = '';
  descricao: string = '';
  quantidade: number = 1;
  gerarCodigo: boolean = true;
  codigosManuais: string = '';
  imageSrc: string | null = null; // Mantido para o preview antigo, caso precise
  selectedFile: File | null = null;
  
  categories: Category[] = [];
  categoryId: number | null = null; 

  ativo: boolean = true;
  validade: string = '';
  nota: number | null = null;

  isUploading: boolean = false;

  // --- VARIÁVEIS PARA O EDITOR DE IMAGEM ---
  imageChangedEvent: any = '';
  croppedImage: any = ''; 

  desiredAmount = signal<number | null>(null);
  calculatedSellingPrice = computed<number>(() => {
      const desired = this.desiredAmount();
      return desired ? this.giftcardService.calculateSellingPrice(desired) : 0;
  });

  constructor(
    private giftcardService: GiftcardService,
    private router: Router,
    private notificationService: NotificationService,
    private categoryService: CategoryService
  ) {
     // Efeito para logar ou reagir a mudanças no preço calculado (opcional)
     effect(() => {
        console.log("Preço de venda calculado:", this.calculatedSellingPrice());
     });
  }

  ngOnInit(): void {
    this.loadCategories();
  }

  loadCategories(): void {
    this.categoryService.getCategories().subscribe({
      next: (data) => { this.categories = data; },
      error: (err) => {
        console.error('Erro ao carregar categorias', err);
      }
    });
  }

  // --- FUNÇÕES DO EDITOR DE IMAGEM ---
  onFileSelected(event: Event): void {
      this.imageChangedEvent = event;
  }

  imageCropped(event: ImageCroppedEvent) {
    this.croppedImage = event.blob;
  }

  loadImageFailed() {
    this.notificationService.show('Não foi possível carregar a imagem. Tente outro arquivo.', 'error');
  }

  toggleGerarCodigo() {
    this.gerarCodigo = !this.gerarCodigo;
    if (!this.gerarCodigo) {
      this.atualizarQuantidadePelosCodigos();
    }
  }

  atualizarQuantidadePelosCodigos(): void {
    if (this.gerarCodigo) return;
    const codigos = this.codigosManuais?.split(';').filter(c => c.trim() !== '') || [];
    this.quantidade = codigos.length;
  }

  onDesiredAmountChange(value: number | null): void {
    this.desiredAmount.set(value);
  }

  onSubmit(): void {
    if (!this.gerarCodigo) {
      this.atualizarQuantidadePelosCodigos();
    }

    const currentDesiredAmount = this.desiredAmount();

    if (!this.titulo || this.quantidade < 1 || currentDesiredAmount === null || currentDesiredAmount <= 0) {
      this.notificationService.show('Preencha Título, Quantidade e um Valor Desejado válido.', 'warning');
      return;
    }

    if (!this.croppedImage) {
        this.notificationService.show('Por favor, selecione e recorte uma imagem para o produto.', 'warning');
        return;
    }

    this.isUploading = true;
    const formData = new FormData();
    formData.append('title', this.titulo);
    // formData.append('valor', this.valorSelecionado.toString()); // <-- Removido
    formData.append('desired_amount', currentDesiredAmount.toString()); // <-- NOVO: Envia o valor desejado
    formData.append('description', this.descricao);
    formData.append('quantityavailable', this.quantidade.toString());
    formData.append('generaterandomly', String(this.gerarCodigo));
    formData.append('ativo', String(this.ativo));
    if (this.categoryId !== null) {
      formData.append('category_id', this.categoryId.toString());
    }
    if (this.validade) {
      formData.append('validade', this.validade);
    }
    if (this.nota !== null) {
      formData.append('nota', this.nota.toString());
    }
    if (!this.gerarCodigo) {
        const validCodes = this.codigosManuais.split(';').filter(c => c.trim() !== '').join(';');
        formData.append('codes', validCodes);
    }

    // Envio da imagem cortada (mantido igual)
    formData.append('image', this.croppedImage, `${this.titulo.replace(/\s+/g, '-')}.jpg`);

    this.giftcardService.createGiftCard(formData).subscribe({
      next: () => {
        this.notificationService.show('Gift Card cadastrado com sucesso!', 'success');
        this.router.navigate(['/dashboard-gc']);
      },
      error: (error) => {
        const errorMessage = error.error?.detail || 'Ocorreu um erro ao cadastrar.';
        this.notificationService.show(errorMessage, 'error');
        this.isUploading = false;
      },
      complete: () => {
        this.isUploading = false;
      }
    });
  }
}