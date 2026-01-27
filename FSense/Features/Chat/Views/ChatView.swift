import SwiftUI
import PhotosUI

/// Main chat view - optimized for performance
struct ChatView: View {

    @StateObject private var viewModel = ChatViewModel()
    @FocusState private var isInputFocused: Bool

    @State private var selectedFlower: Flower?
    @State private var navigateToFlowerDetail = false
    @State private var showImagePicker = false
    @State private var selectedPhotoItem: PhotosPickerItem?

    var body: some View {
        NavigationStack {
            VStack(spacing: 0) {
                messagesScrollView
                chatInputView
            }
            .background(Color(white: 0.97))
            .navigationBarHidden(true)
            .navigationDestination(isPresented: $navigateToFlowerDetail) {
                if let flower = selectedFlower {
                    FlowerCardView(flower: flower)
                        .id(flower.id)
                }
            }
        }
        .onAppear {
            viewModel.send(.onAppear)
        }
    }

    // MARK: - Messages (Optimized with cached precomputed data)

    private var messagesScrollView: some View {
        ScrollView(showsIndicators: false) {
            LazyVStack(spacing: 16) {
                let messages = viewModel.orderedMessages
                let precomputed = viewModel.precomputedMessageData
                let steps = viewModel.pipelineSteps

                // Use indices to avoid Array() allocation - preserves LazyVStack laziness
                ForEach(messages.indices, id: \.self) { index in
                    let message = messages[index]
                    let data = index < precomputed.count
                        ? precomputed[index]
                        : ChatViewModel.MessageRowData(thinkingId: message.id, hideCompletedThinking: false)

                    ChatMessageRow(
                        message: message,
                        steps: steps,
                        isThinkingExpanded: viewModel.isThinkingCardExpanded(data.thinkingId),
                        thinkingId: data.thinkingId,
                        hideCompletedThinking: data.hideCompletedThinking,
                        onThinkingToggle: viewModel.send,
                        onExploreFlower: handleExploreFlower
                    )
                    .id(message.id)
                }
            }
            .padding(.horizontal, 16)
            .padding(.top, 16)
            .padding(.bottom, 8)
        }
        .defaultScrollAnchor(.bottom)
    }

    private func handleExploreFlower(_ recommendation: FlowerRecommendation) {
        if let payload = viewModel.lastPayload {
            print("[ChatView] Using real payload for: \(payload.header.name)")
            selectedFlower = payload.toFlower()
            print("[ChatView] Created flower with giftingInfo: \(selectedFlower?.giftingInfo != nil)")
        } else {
            print("[ChatView] WARNING: No payload! Using fallback for: \(recommendation.flowerName)")
            selectedFlower = Flower(
                name: recommendation.flowerName,
                imageAsset: recommendation.imageAsset,
                meanings: ["Love", "Appreciation"],
                symbolismText: recommendation.explanation,
                whyThisFlowerText: recommendation.meaning,
                moodIntensityValue: 0.7
            )
        }
        navigateToFlowerDetail = true
    }

    // MARK: - Chat Message Row Helper

    private struct ChatMessageRow: View {
        let message: ChatMessage
        let steps: [ProgressStep]
        let isThinkingExpanded: Bool
        let thinkingId: UUID
        let hideCompletedThinking: Bool
        let onThinkingToggle: (ChatAction) -> Void
        var onExploreFlower: ((FlowerRecommendation) -> Void)?

        var body: some View {
            MessageBubbleView(
                message: message,
                steps: steps,
                isThinkingExpanded: isThinkingExpanded,
                onThinkingToggle: { onThinkingToggle(.toggleThinkingCard(thinkingId)) },
                onExploreFlower: onExploreFlower,
                hideCompletedThinking: hideCompletedThinking
            )
        }
    }

    // MARK: - Input (with direct binding - no action dispatch per keystroke)

    private var chatInputView: some View {
        VStack(spacing: 0) {
            Divider()

            // Show attachment preview if image is attached
            if let attachedImage = viewModel.attachedImage {
                HStack {
                    Image(uiImage: attachedImage)
                        .resizable()
                        .aspectRatio(contentMode: .fill)
                        .frame(width: 60, height: 60)
                        .clipShape(RoundedRectangle(cornerRadius: 8))
                        .overlay(alignment: .topTrailing) {
                            Button {
                                viewModel.send(.removeAttachment)
                            } label: {
                                Image(systemName: "xmark.circle.fill")
                                    .font(.system(size: 18))
                                    .foregroundColor(.white)
                                    .background(Circle().fill(Color.black.opacity(0.6)))
                            }
                            .offset(x: 6, y: -6)
                        }

                    Text("Image attached")
                        .font(.system(size: 13))
                        .foregroundColor(.secondary)

                    Spacer()
                }
                .padding(.horizontal, 16)
                .padding(.top, 12)
                .padding(.bottom, 8)
            }

            HStack(spacing: 12) {
                // Image picker button
                PhotosPicker(selection: $selectedPhotoItem, matching: .images) {
                    Image(systemName: "photo")
                        .font(.system(size: 18))
                        .foregroundColor(.purple)
                        .frame(width: 36, height: 36)
                }
                .onChange(of: selectedPhotoItem) { oldValue, newValue in
                    Task {
                        if let item = newValue,
                           let data = try? await item.loadTransferable(type: Data.self),
                           let image = UIImage(data: data) {
                            viewModel.send(.attachImage(image))
                        }
                    }
                }
                .disabled(!viewModel.isInputEnabled)

                HStack(spacing: 8) {
                    // Direct binding to viewModel.inputText - no action dispatch per keystroke
                    TextField("Ask me about flowers...", text: $viewModel.inputText)
                        .font(.system(size: 16))
                        .focused($isInputFocused)
                        .disabled(!viewModel.isInputEnabled)
                        .submitLabel(.send)
                        .onSubmit {
                            if viewModel.canSendMessage {
                                viewModel.send(.sendMessage)
                            }
                        }

                    Button {
                        viewModel.send(.sendMessage)
                        isInputFocused = false
                    } label: {
                        Image(systemName: "arrow.up")
                            .font(.system(size: 14, weight: .bold))
                            .foregroundColor(.white)
                            .frame(width: 30, height: 30)
                            .background(
                                Circle().fill(Color.purple.opacity(viewModel.canSendMessage ? 1 : 0.4))
                            )
                    }
                    .disabled(!viewModel.canSendMessage)
                }
                .padding(.leading, 16)
                .padding(.trailing, 8)
                .padding(.vertical, 8)
                .background(Capsule().fill(Color(white: 0.95)))
            }
            .padding(.horizontal, 16)
            .padding(.vertical, 12)
            .background(Color.white)
        }
    }
}
