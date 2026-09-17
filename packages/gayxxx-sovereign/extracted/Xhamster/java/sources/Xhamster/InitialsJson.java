package Xhamster;

/* JADX INFO: compiled from: Xhamster.kt */
/* JADX INFO: loaded from: classes.dex */
@kotlin.Metadata(d1 = {"\u0000D\n\u0002\u0018\u0002\n\u0002\u0010\u0000\n\u0000\n\u0002\u0018\u0002\n\u0000\n\u0002\u0018\u0002\n\u0000\n\u0002\u0018\u0002\n\u0000\n\u0002\u0018\u0002\n\u0000\n\u0002\u0018\u0002\n\u0000\n\u0002\u0018\u0002\n\u0002\b\u0016\n\u0002\u0010\u000b\n\u0002\b\u0002\n\u0002\u0010\b\n\u0000\n\u0002\u0010\u000e\n\u0000\b\u0086\b\u0018\u00002\u00020\u0001BO\u0012\n\b\u0002\u0010\u0002\u001a\u0004\u0018\u00010\u0003\u0012\n\b\u0002\u0010\u0004\u001a\u0004\u0018\u00010\u0005\u0012\n\b\u0002\u0010\u0006\u001a\u0004\u0018\u00010\u0007\u0012\n\b\u0002\u0010\b\u001a\u0004\u0018\u00010\t\u0012\n\b\u0002\u0010\n\u001a\u0004\u0018\u00010\u000b\u0012\n\b\u0002\u0010\f\u001a\u0004\u0018\u00010\r¢\u0006\u0004\b\u000e\u0010\u000fJ\u000b\u0010\u001c\u001a\u0004\u0018\u00010\u0003HÆ\u0003J\u000b\u0010\u001d\u001a\u0004\u0018\u00010\u0005HÆ\u0003J\u000b\u0010\u001e\u001a\u0004\u0018\u00010\u0007HÆ\u0003J\u000b\u0010\u001f\u001a\u0004\u0018\u00010\tHÆ\u0003J\u000b\u0010 \u001a\u0004\u0018\u00010\u000bHÆ\u0003J\u000b\u0010!\u001a\u0004\u0018\u00010\rHÆ\u0003JQ\u0010\"\u001a\u00020\u00002\n\b\u0002\u0010\u0002\u001a\u0004\u0018\u00010\u00032\n\b\u0002\u0010\u0004\u001a\u0004\u0018\u00010\u00052\n\b\u0002\u0010\u0006\u001a\u0004\u0018\u00010\u00072\n\b\u0002\u0010\b\u001a\u0004\u0018\u00010\t2\n\b\u0002\u0010\n\u001a\u0004\u0018\u00010\u000b2\n\b\u0002\u0010\f\u001a\u0004\u0018\u00010\rHÆ\u0001J\u0014\u0010#\u001a\u00020$2\b\u0010%\u001a\u0004\u0018\u00010\u0001HÖ\u0083\u0004J\n\u0010&\u001a\u00020'HÖ\u0081\u0004J\n\u0010(\u001a\u00020)HÖ\u0081\u0004R\u0013\u0010\u0002\u001a\u0004\u0018\u00010\u0003¢\u0006\b\n\u0000\u001a\u0004\b\u0010\u0010\u0011R\u0013\u0010\u0004\u001a\u0004\u0018\u00010\u0005¢\u0006\b\n\u0000\u001a\u0004\b\u0012\u0010\u0013R\u0013\u0010\u0006\u001a\u0004\u0018\u00010\u0007¢\u0006\b\n\u0000\u001a\u0004\b\u0014\u0010\u0015R\u0013\u0010\b\u001a\u0004\u0018\u00010\t¢\u0006\b\n\u0000\u001a\u0004\b\u0016\u0010\u0017R\u0013\u0010\n\u001a\u0004\u0018\u00010\u000b¢\u0006\b\n\u0000\u001a\u0004\b\u0018\u0010\u0019R\u0013\u0010\f\u001a\u0004\u0018\u00010\r¢\u0006\b\n\u0000\u001a\u0004\b\u001a\u0010\u001b¨\u0006*"}, d2 = {"LXhamster/InitialsJson;", "", "xplayerSettings", "LXhamster/XPlayerSettings;", "videoEntity", "LXhamster/VideoEntity;", "videoTagsComponent", "LXhamster/VideoTagsComponent;", "relatedVideos", "LXhamster/RelatedVideos;", "layoutPage", "LXhamster/LayoutPage;", "searchResult", "LXhamster/SearchResult;", "<init>", "(LXhamster/XPlayerSettings;LXhamster/VideoEntity;LXhamster/VideoTagsComponent;LXhamster/RelatedVideos;LXhamster/LayoutPage;LXhamster/SearchResult;)V", "getXplayerSettings", "()LXhamster/XPlayerSettings;", "getVideoEntity", "()LXhamster/VideoEntity;", "getVideoTagsComponent", "()LXhamster/VideoTagsComponent;", "getRelatedVideos", "()LXhamster/RelatedVideos;", "getLayoutPage", "()LXhamster/LayoutPage;", "getSearchResult", "()LXhamster/SearchResult;", "component1", "component2", "component3", "component4", "component5", "component6", "copy", "equals", "", "other", "hashCode", "", "toString", "", "Xhamster"}, k = 1, mv = {2, 3, 0}, xi = 48)
public final /* data */ class InitialsJson {

    @org.jetbrains.annotations.Nullable
    private final Xhamster.LayoutPage layoutPage;

    @org.jetbrains.annotations.Nullable
    private final Xhamster.RelatedVideos relatedVideos;

    @org.jetbrains.annotations.Nullable
    private final Xhamster.SearchResult searchResult;

    @org.jetbrains.annotations.Nullable
    private final Xhamster.VideoEntity videoEntity;

    @org.jetbrains.annotations.Nullable
    private final Xhamster.VideoTagsComponent videoTagsComponent;

    @org.jetbrains.annotations.Nullable
    private final Xhamster.XPlayerSettings xplayerSettings;

    public InitialsJson() {
        this(null, null, null, null, null, null, 63, null);
    }

    public static /* synthetic */ Xhamster.InitialsJson copy$default(Xhamster.InitialsJson initialsJson, Xhamster.XPlayerSettings xPlayerSettings, Xhamster.VideoEntity videoEntity, Xhamster.VideoTagsComponent videoTagsComponent, Xhamster.RelatedVideos relatedVideos, Xhamster.LayoutPage layoutPage, Xhamster.SearchResult searchResult, int i, java.lang.Object obj) {
        if ((i & 1) != 0) {
            xPlayerSettings = initialsJson.xplayerSettings;
        }
        if ((i & 2) != 0) {
            videoEntity = initialsJson.videoEntity;
        }
        if ((i & 4) != 0) {
            videoTagsComponent = initialsJson.videoTagsComponent;
        }
        if ((i & 8) != 0) {
            relatedVideos = initialsJson.relatedVideos;
        }
        if ((i & 16) != 0) {
            layoutPage = initialsJson.layoutPage;
        }
        if ((i & 32) != 0) {
            searchResult = initialsJson.searchResult;
        }
        Xhamster.LayoutPage layoutPage2 = layoutPage;
        Xhamster.SearchResult searchResult2 = searchResult;
        return initialsJson.copy(xPlayerSettings, videoEntity, videoTagsComponent, relatedVideos, layoutPage2, searchResult2);
    }

    @org.jetbrains.annotations.Nullable
    /* JADX INFO: renamed from: component1, reason: from getter */
    public final Xhamster.XPlayerSettings getXplayerSettings() {
        return this.xplayerSettings;
    }

    @org.jetbrains.annotations.Nullable
    /* JADX INFO: renamed from: component2, reason: from getter */
    public final Xhamster.VideoEntity getVideoEntity() {
        return this.videoEntity;
    }

    @org.jetbrains.annotations.Nullable
    /* JADX INFO: renamed from: component3, reason: from getter */
    public final Xhamster.VideoTagsComponent getVideoTagsComponent() {
        return this.videoTagsComponent;
    }

    @org.jetbrains.annotations.Nullable
    /* JADX INFO: renamed from: component4, reason: from getter */
    public final Xhamster.RelatedVideos getRelatedVideos() {
        return this.relatedVideos;
    }

    @org.jetbrains.annotations.Nullable
    /* JADX INFO: renamed from: component5, reason: from getter */
    public final Xhamster.LayoutPage getLayoutPage() {
        return this.layoutPage;
    }

    @org.jetbrains.annotations.Nullable
    /* JADX INFO: renamed from: component6, reason: from getter */
    public final Xhamster.SearchResult getSearchResult() {
        return this.searchResult;
    }

    @org.jetbrains.annotations.NotNull
    public final Xhamster.InitialsJson copy(@org.jetbrains.annotations.Nullable Xhamster.XPlayerSettings xplayerSettings, @org.jetbrains.annotations.Nullable Xhamster.VideoEntity videoEntity, @org.jetbrains.annotations.Nullable Xhamster.VideoTagsComponent videoTagsComponent, @org.jetbrains.annotations.Nullable Xhamster.RelatedVideos relatedVideos, @org.jetbrains.annotations.Nullable Xhamster.LayoutPage layoutPage, @org.jetbrains.annotations.Nullable Xhamster.SearchResult searchResult) {
        return new Xhamster.InitialsJson(xplayerSettings, videoEntity, videoTagsComponent, relatedVideos, layoutPage, searchResult);
    }

    public boolean equals(@org.jetbrains.annotations.Nullable java.lang.Object other) {
        if (this == other) {
            return true;
        }
        if (!(other instanceof Xhamster.InitialsJson)) {
            return false;
        }
        Xhamster.InitialsJson initialsJson = (Xhamster.InitialsJson) other;
        return kotlin.jvm.internal.Intrinsics.areEqual(this.xplayerSettings, initialsJson.xplayerSettings) && kotlin.jvm.internal.Intrinsics.areEqual(this.videoEntity, initialsJson.videoEntity) && kotlin.jvm.internal.Intrinsics.areEqual(this.videoTagsComponent, initialsJson.videoTagsComponent) && kotlin.jvm.internal.Intrinsics.areEqual(this.relatedVideos, initialsJson.relatedVideos) && kotlin.jvm.internal.Intrinsics.areEqual(this.layoutPage, initialsJson.layoutPage) && kotlin.jvm.internal.Intrinsics.areEqual(this.searchResult, initialsJson.searchResult);
    }

    public int hashCode() {
        return ((((((((((this.xplayerSettings == null ? 0 : this.xplayerSettings.hashCode()) * 31) + (this.videoEntity == null ? 0 : this.videoEntity.hashCode())) * 31) + (this.videoTagsComponent == null ? 0 : this.videoTagsComponent.hashCode())) * 31) + (this.relatedVideos == null ? 0 : this.relatedVideos.hashCode())) * 31) + (this.layoutPage == null ? 0 : this.layoutPage.hashCode())) * 31) + (this.searchResult != null ? this.searchResult.hashCode() : 0);
    }

    @org.jetbrains.annotations.NotNull
    public java.lang.String toString() {
        return "InitialsJson(xplayerSettings=" + this.xplayerSettings + ", videoEntity=" + this.videoEntity + ", videoTagsComponent=" + this.videoTagsComponent + ", relatedVideos=" + this.relatedVideos + ", layoutPage=" + this.layoutPage + ", searchResult=" + this.searchResult + ')';
    }

    public InitialsJson(@org.jetbrains.annotations.Nullable Xhamster.XPlayerSettings xplayerSettings, @org.jetbrains.annotations.Nullable Xhamster.VideoEntity videoEntity, @org.jetbrains.annotations.Nullable Xhamster.VideoTagsComponent videoTagsComponent, @org.jetbrains.annotations.Nullable Xhamster.RelatedVideos relatedVideos, @org.jetbrains.annotations.Nullable Xhamster.LayoutPage layoutPage, @org.jetbrains.annotations.Nullable Xhamster.SearchResult searchResult) {
        this.xplayerSettings = xplayerSettings;
        this.videoEntity = videoEntity;
        this.videoTagsComponent = videoTagsComponent;
        this.relatedVideos = relatedVideos;
        this.layoutPage = layoutPage;
        this.searchResult = searchResult;
    }

    public /* synthetic */ InitialsJson(Xhamster.XPlayerSettings xPlayerSettings, Xhamster.VideoEntity videoEntity, Xhamster.VideoTagsComponent videoTagsComponent, Xhamster.RelatedVideos relatedVideos, Xhamster.LayoutPage layoutPage, Xhamster.SearchResult searchResult, int i, kotlin.jvm.internal.DefaultConstructorMarker defaultConstructorMarker) {
        this((i & 1) != 0 ? null : xPlayerSettings, (i & 2) != 0 ? null : videoEntity, (i & 4) != 0 ? null : videoTagsComponent, (i & 8) != 0 ? null : relatedVideos, (i & 16) != 0 ? null : layoutPage, (i & 32) != 0 ? null : searchResult);
    }

    @org.jetbrains.annotations.Nullable
    public final Xhamster.XPlayerSettings getXplayerSettings() {
        return this.xplayerSettings;
    }

    @org.jetbrains.annotations.Nullable
    public final Xhamster.VideoEntity getVideoEntity() {
        return this.videoEntity;
    }

    @org.jetbrains.annotations.Nullable
    public final Xhamster.VideoTagsComponent getVideoTagsComponent() {
        return this.videoTagsComponent;
    }

    @org.jetbrains.annotations.Nullable
    public final Xhamster.RelatedVideos getRelatedVideos() {
        return this.relatedVideos;
    }

    @org.jetbrains.annotations.Nullable
    public final Xhamster.LayoutPage getLayoutPage() {
        return this.layoutPage;
    }

    @org.jetbrains.annotations.Nullable
    public final Xhamster.SearchResult getSearchResult() {
        return this.searchResult;
    }
}
