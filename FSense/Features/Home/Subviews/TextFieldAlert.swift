import SwiftUI

/// A reusable text field alert for renaming operations
struct TextFieldAlert {
    let title: String
    let message: String
    let placeholder: String
    let initialText: String
    let confirmButtonTitle: String
    let onConfirm: (String) -> Void

    func present(in viewController: UIViewController) {
        let alert = UIAlertController(
            title: title,
            message: message,
            preferredStyle: .alert
        )

        alert.addTextField { textField in
            textField.placeholder = placeholder
            textField.text = initialText
            textField.autocapitalizationType = .sentences
        }

        let confirmAction = UIAlertAction(title: confirmButtonTitle, style: .default) { _ in
            guard let textField = alert.textFields?.first,
                  let text = textField.text,
                  !text.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else {
                return
            }
            onConfirm(text)
        }

        let cancelAction = UIAlertAction(title: "Cancel", style: .cancel)

        alert.addAction(confirmAction)
        alert.addAction(cancelAction)

        viewController.present(alert, animated: true)
    }
}

/// View modifier to present text field alert
struct TextFieldAlertModifier: ViewModifier {
    @Binding var isPresented: Bool
    let title: String
    let message: String
    let placeholder: String
    let initialText: String
    let confirmButtonTitle: String
    let onConfirm: (String) -> Void

    func body(content: Content) -> some View {
        content
            .onChange(of: isPresented) { _, newValue in
                if newValue {
                    presentAlert()
                }
            }
    }

    private func presentAlert() {
        guard let windowScene = UIApplication.shared.connectedScenes.first as? UIWindowScene,
              let viewController = windowScene.windows.first?.rootViewController else {
            isPresented = false
            return
        }

        let alert = TextFieldAlert(
            title: title,
            message: message,
            placeholder: placeholder,
            initialText: initialText,
            confirmButtonTitle: confirmButtonTitle,
            onConfirm: { text in
                onConfirm(text)
                isPresented = false
            }
        )

        alert.present(in: viewController)
    }
}

extension View {
    func textFieldAlert(
        isPresented: Binding<Bool>,
        title: String,
        message: String = "",
        placeholder: String = "",
        initialText: String = "",
        confirmButtonTitle: String = "OK",
        onConfirm: @escaping (String) -> Void
    ) -> some View {
        modifier(TextFieldAlertModifier(
            isPresented: isPresented,
            title: title,
            message: message,
            placeholder: placeholder,
            initialText: initialText,
            confirmButtonTitle: confirmButtonTitle,
            onConfirm: onConfirm
        ))
    }
}
