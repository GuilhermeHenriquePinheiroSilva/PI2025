import { ComponentFixture, TestBed } from '@angular/core/testing';

import { EditGcComponent } from './edit-gc.component';

describe('EditGcComponent', () => {
  let component: EditGcComponent;
  let fixture: ComponentFixture<EditGcComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [EditGcComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(EditGcComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
